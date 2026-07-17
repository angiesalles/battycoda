"""
Memory-efficient HDF5 spectrogram generation using chunked processing.

This module processes large audio files in fixed-size sample chunks to avoid
loading the entire file into memory, preventing out-of-memory crashes for
large or high-sample-rate recordings.
"""

import h5py
import librosa
import numpy as np
import soundfile as sf

# Spectrogram parameters
N_FFT = 512
HOP_LENGTH = N_FFT // 4
N_FREQ_BINS = N_FFT // 2 + 1

# Chunks are a fixed number of SAMPLES, not seconds. A "60 second" chunk of
# 384 kHz bat audio is 23M samples, which peaked ~2.4 GB per task once the
# float64 STFT temporaries stacked up. 2M samples bounds peak working memory
# to ~100 MB regardless of sample rate.
CHUNK_SAMPLES = 2_000_000

# Quiet bins floor at -80 dB (amplitude amin=1e-4). This replaces the old
# per-chunk `ref=np.max` normalization, which gave every chunk its own
# reference level (brightness seams at chunk boundaries). Absolute dB with a
# fixed floor is chunk-independent; the viewer min/max-normalizes each
# rendered window, and its silence padding value (-80) matches this floor.
DB_AMIN = 1e-4


def _spectrogram_frames(buffer):
    """
    Convert all complete STFT frames at the start of `buffer` to float16 dB.

    Framing is done with center=False on an explicitly padded stream (see
    caller), which reproduces librosa.stft(center=True, pad_mode="constant")
    frame-for-frame no matter how the audio was chunked.

    Returns:
        (db_chunk, leftover): float16 array of shape (N_FREQ_BINS, n) or None
        if no complete frame fits, and the unconsumed tail of the buffer.
    """
    if len(buffer) < N_FFT:
        return None, buffer

    n_frames = (len(buffer) - N_FFT) // HOP_LENGTH + 1
    usable = (n_frames - 1) * HOP_LENGTH + N_FFT

    stft_chunk = librosa.stft(buffer[:usable], n_fft=N_FFT, hop_length=HOP_LENGTH, center=False)
    db_chunk = librosa.amplitude_to_db(np.abs(stft_chunk), ref=1.0, amin=DB_AMIN, top_db=None)

    return db_chunk.astype(np.float16), buffer[n_frames * HOP_LENGTH :]


def generate_hdf5_spectrogram_chunked(wav_path, output_path, progress_callback=None, chunk_samples=CHUNK_SAMPLES):
    """
    Generate HDF5 spectrogram by streaming audio in fixed-size sample chunks.

    Audio is read as float32 (bit-exact for 16-bit PCM sources) and processed
    through a carry buffer so the concatenated output is identical to a
    single-shot librosa.stft(center=True) over the whole file. Each chunk is
    appended to the HDF5 file incrementally.

    Args:
        wav_path: Path to input WAV file
        output_path: Path to output HDF5 file
        progress_callback: Optional callback function(progress_percent)
        chunk_samples: Samples per read; bounds peak memory use

    Returns:
        dict: Result with metadata about the generated spectrogram
    """
    # Get audio file info WITHOUT loading the entire file
    audio_info = sf.info(wav_path)
    sample_rate = audio_info.samplerate
    total_frames = audio_info.frames
    channels = audio_info.channels

    if progress_callback:
        progress_callback(30)

    # Determine if we need to downsample for very long files (>10 minutes)
    max_duration_samples = 10 * 60 * sample_rate
    if total_frames > max_duration_samples:
        downsample_factor = int(total_frames / max_duration_samples) + 1
        effective_sample_rate = sample_rate / downsample_factor
    else:
        downsample_factor = 1
        effective_sample_rate = sample_rate

    if progress_callback:
        progress_callback(40)

    pad = N_FFT // 2

    # Create HDF5 file with resizable dataset for streaming writes
    with h5py.File(output_path, "w") as f:
        # Create resizable dataset (we don't know final size yet)
        dataset = f.create_dataset(
            "spectrogram",
            shape=(N_FREQ_BINS, 0),  # Start with 0 columns
            maxshape=(N_FREQ_BINS, None),  # Unlimited columns
            dtype="float16",
            compression="gzip",
            compression_opts=9,
            chunks=(N_FREQ_BINS, 100),  # Chunk size for HDF5 storage
        )

        total_written_frames = 0
        frames_processed = 0

        def write_frames(db_chunk):
            nonlocal total_written_frames
            new_size = total_written_frames + db_chunk.shape[1]
            dataset.resize((N_FREQ_BINS, new_size))
            dataset[:, total_written_frames:new_size] = db_chunk
            total_written_frames = new_size

        # The buffer holds the not-yet-framed part of the (downsampled,
        # zero-padded) signal. Seeding it with the left pad and appending the
        # right pad after EOF emulates librosa's center=True zero padding.
        buffer = np.zeros(pad, dtype=np.float32)

        # Read and process audio in chunks
        with sf.SoundFile(wav_path, "r") as audio_file:
            while frames_processed < total_frames:
                frames_to_read = min(chunk_samples, total_frames - frames_processed)
                audio_chunk = audio_file.read(frames_to_read, dtype="float32")

                # Convert stereo to mono if needed
                if channels > 1:
                    audio_chunk = np.mean(audio_chunk, axis=1)

                # Downsample if needed, keeping decimation phase aligned
                # across chunk boundaries
                if downsample_factor > 1:
                    offset = (-frames_processed) % downsample_factor
                    audio_chunk = audio_chunk[offset::downsample_factor]

                frames_processed += frames_to_read

                buffer = np.concatenate([buffer, audio_chunk])
                db_chunk, buffer = _spectrogram_frames(buffer)
                if db_chunk is not None:
                    write_frames(db_chunk)

                # Update progress (40-80%)
                if progress_callback:
                    progress = 40 + int(40 * frames_processed / total_frames)
                    progress_callback(progress)

        # Append the right pad and flush the remaining frames
        buffer = np.concatenate([buffer, np.zeros(pad, dtype=np.float32)])
        db_chunk, buffer = _spectrogram_frames(buffer)
        if db_chunk is not None:
            write_frames(db_chunk)

        # Store metadata
        f.attrs["sample_rate"] = effective_sample_rate
        f.attrs["n_fft"] = N_FFT
        f.attrs["hop_length"] = HOP_LENGTH
        f.attrs["duration"] = total_frames / sample_rate
        f.attrs["n_frames"] = total_written_frames
        f.attrs["n_freq_bins"] = N_FREQ_BINS

    if progress_callback:
        progress_callback(80)

    return {
        "status": "success",
        "file_path": output_path,
        "shape": (N_FREQ_BINS, total_written_frames),
        "duration": total_frames / sample_rate,
        "sample_rate": effective_sample_rate,
    }
