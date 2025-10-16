"""
Memory-efficient HDF5 spectrogram generation using chunked processing.

This module processes large audio files in chunks to avoid loading the entire
file into memory, preventing out-of-memory crashes for large recordings (>500MB).
"""
import os
import numpy as np
import soundfile as sf
import librosa
import h5py


def generate_hdf5_spectrogram_chunked(wav_path, output_path, progress_callback=None):
    """
    Generate HDF5 spectrogram by processing audio in chunks.

    This method processes the audio file in 60-second chunks to avoid loading
    the entire file into memory. Each chunk is processed and appended to the
    HDF5 file incrementally.

    Args:
        wav_path: Path to input WAV file
        output_path: Path to output HDF5 file
        progress_callback: Optional callback function(progress_percent) for progress updates

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

    # Spectrogram parameters
    hop_length = 512
    n_fft = 2048
    chunk_duration = 60  # Process 60 seconds at a time
    chunk_size = int(chunk_duration * sample_rate)

    # Calculate frequency bins to keep (up to 128kHz)
    max_freq_hz = 128000
    freq_per_bin = (effective_sample_rate / 2) / (n_fft / 2)
    max_bin = int(max_freq_hz / freq_per_bin)
    # STFT produces n_fft // 2 + 1 bins, so limit max_bin to actual available bins
    actual_bins = n_fft // 2 + 1
    max_bin = min(max_bin, actual_bins)

    # Create HDF5 file with resizable dataset for streaming writes
    with h5py.File(output_path, 'w') as f:
        # Create resizable dataset (we don't know final size yet)
        dataset = f.create_dataset(
            'spectrogram',
            shape=(max_bin, 0),  # Start with 0 columns
            maxshape=(max_bin, None),  # Unlimited columns
            dtype='float16',
            compression='gzip',
            compression_opts=9,
            chunks=(max_bin, 100)  # Chunk size for HDF5 storage
        )

        total_written_frames = 0
        frames_processed = 0

        # Read and process audio in chunks
        with sf.SoundFile(wav_path, 'r') as audio_file:
            while frames_processed < total_frames:
                # Read chunk
                frames_to_read = min(chunk_size, total_frames - frames_processed)
                audio_chunk = audio_file.read(frames_to_read)

                # Convert stereo to mono if needed
                if channels > 1:
                    audio_chunk = np.mean(audio_chunk, axis=1)

                # Downsample if needed
                if downsample_factor > 1:
                    audio_chunk = audio_chunk[::downsample_factor]

                # Compute STFT for this chunk
                stft_chunk = librosa.stft(audio_chunk, hop_length=hop_length, n_fft=n_fft)
                spec_chunk = librosa.amplitude_to_db(np.abs(stft_chunk), ref=np.max)

                # Limit frequency range
                spec_chunk = spec_chunk[:max_bin, :]
                spec_chunk = spec_chunk.astype(np.float16)

                # Resize dataset and append chunk
                new_size = total_written_frames + spec_chunk.shape[1]
                dataset.resize((max_bin, new_size))
                dataset[:, total_written_frames:new_size] = spec_chunk

                total_written_frames = new_size
                frames_processed += frames_to_read

                # Update progress (40-80%)
                if progress_callback:
                    progress = 40 + int(40 * frames_processed / total_frames)
                    progress_callback(progress)

        # Store metadata
        f.attrs['sample_rate'] = effective_sample_rate
        f.attrs['hop_length'] = hop_length
        f.attrs['n_fft'] = n_fft
        f.attrs['duration'] = total_frames / sample_rate
        f.attrs['n_frames'] = total_written_frames
        f.attrs['n_freq_bins'] = max_bin

    if progress_callback:
        progress_callback(80)

    return {
        'status': 'success',
        'file_path': output_path,
        'shape': (max_bin, total_written_frames),
        'duration': total_frames / sample_rate,
        'sample_rate': effective_sample_rate
    }
