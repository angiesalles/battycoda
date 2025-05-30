# coding: utf-8

"""
    BattyCoda API

    API for BattyCoda - Animal Call Analysis Platform

    The version of the OpenAPI document: 1.0.0
    Generated by OpenAPI Generator (https://openapi-generator.tech)

    Do not edit the class manually.
"""  # noqa: E501


import unittest

from openapi_client.models.task import Task

class TestTask(unittest.TestCase):
    """Task unit test stubs"""

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def make_instance(self, include_optional) -> Task:
        """Test Task
            include_optional is a boolean, when False only required
            params are included, when True both required and
            optional params are included """
        # uncomment below to create an instance of `Task`
        """
        model = Task()
        if include_optional:
            return Task(
                id = 56,
                batch = openapi_client.models.task_batch.TaskBatch(
                    id = 56, 
                    name = '', 
                    description = '', 
                    species = null, 
                    total_tasks = '', 
                    completed_tasks = '', 
                    pending_tasks = '', 
                    progress_percentage = '', 
                    created_at = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), ),
                status = 'pending',
                onset = 1.337,
                offset = 1.337,
                label = '',
                notes = '',
                created_at = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'),
                updated_at = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f')
            )
        else:
            return Task(
                id = 56,
                batch = openapi_client.models.task_batch.TaskBatch(
                    id = 56, 
                    name = '', 
                    description = '', 
                    species = null, 
                    total_tasks = '', 
                    completed_tasks = '', 
                    pending_tasks = '', 
                    progress_percentage = '', 
                    created_at = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'), ),
                onset = 1.337,
                offset = 1.337,
                created_at = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'),
                updated_at = datetime.datetime.strptime('2013-10-20 19:20:30.00', '%Y-%m-%d %H:%M:%S.%f'),
        )
        """

    def testTask(self):
        """Test Task"""
        # inst_req_only = self.make_instance(include_optional=False)
        # inst_req_and_optional = self.make_instance(include_optional=True)

if __name__ == '__main__':
    unittest.main()
