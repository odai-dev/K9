import pytest
import json
from datetime import date, timedelta
from flask import url_for


@pytest.mark.integration 
@pytest.mark.database
class TestFeedingReportsIntegration:
    """Integration tests for feeding reports system"""

    def test_complete_daily_report_workflow(self, authenticated_client, test_feeding_logs, test_project, test_dogs):
        """Test complete workflow from route to API to data display"""
        target_date = date.today()
        
        # Step 1: Access the daily report page
        page_response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        assert page_response.status_code == 200
        
        # Step 2: Fetch data via API
        api_response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        assert api_response.status_code == 200
        
        # Step 3: Verify data consistency
        data = json.loads(api_response.data)
        assert data['success'] is True
        assert len(data['rows']) > 0  # Should have feeding data
        
        # Step 4: Test with dog filter
        test_dog = test_dogs[0]
        filtered_response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'dog_id': test_dog.id
            }
        )
        assert filtered_response.status_code == 200
        filtered_data = json.loads(filtered_response.data)
        
        # All rows should be for the specified dog
        for row in filtered_data['rows']:
            assert row['dog_id'] == str(test_dog.id)

    def test_complete_weekly_report_workflow(self, authenticated_client, test_feeding_logs, test_project):
        """Test complete workflow for weekly reports"""
        week_start = date.today() - timedelta(days=6)
        
        # Step 1: Access the weekly report page
        page_response = authenticated_client.get(
            '/breeding/feeding-reports/weekly',
            query_string={'project_id': test_project.id}
        )
        assert page_response.status_code == 200
        
        # Step 2: Fetch data via API
        api_response = authenticated_client.get(
            '/api/breeding/feeding-reports/weekly',
            query_string={
                'project_id': test_project.id,
                'week_start': week_start.strftime('%Y-%m-%d')
            }
        )
        assert api_response.status_code == 200

    def test_pagination_across_large_dataset(self, authenticated_client, test_project, test_dogs, db_session):
        """Test pagination with larger dataset"""
        from k9.models.models import FeedingLog, PrepMethod, BodyConditionScale
        from datetime import datetime
        
        # Create larger dataset
        target_date = date.today()
        for i in range(50):  # Create 50 additional feeding logs
            log = FeedingLog(
                project_id=test_project.id,
                dog_id=test_dogs[i % len(test_dogs)].id,
                date=target_date,
                time=datetime.strptime(f'{8 + (i % 12):02d}:00:00', '%H:%M:%S').time(),
                meal_name=f'Test Meal {i}',
                grams=200 + i,
                water_ml=100 + i,
                meal_type_fresh=True,
                meal_type_dry=False,
                prep_method=PrepMethod.BOILED,
                body_condition=BodyConditionScale.IDEAL
            )
            db_session.add(log)
        db_session.commit()
        
        # Test first page
        response1 = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'page': 1,
                'per_page': 20
            }
        )
        assert response1.status_code == 200
        data1 = json.loads(response1.data)
        
        # Test second page
        response2 = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'page': 2,
                'per_page': 20
            }
        )
        assert response2.status_code == 200
        data2 = json.loads(response2.data)
        
        # Verify pagination metadata
        assert data1['pagination']['page'] == 1
        assert data2['pagination']['page'] == 2
        assert data1['pagination']['has_next'] is True
        assert data2['pagination']['has_prev'] is True
        
        # Verify different data on different pages
        page1_ids = {row['dog_id'] + row['time'] for row in data1['rows']}
        page2_ids = {row['dog_id'] + row['time'] for row in data2['rows']}
        assert len(page1_ids.intersection(page2_ids)) == 0  # No overlap

    def test_performance_optimization_effectiveness(self, authenticated_client, test_project, test_dogs, db_session):
        """Test that performance optimizations work effectively"""
        from k9.models.models import FeedingLog, PrepMethod, BodyConditionScale
        from datetime import datetime
        import time
        
        # Create substantial dataset
        target_date = date.today()
        for i in range(100):
            log = FeedingLog(
                project_id=test_project.id,
                dog_id=test_dogs[i % len(test_dogs)].id,
                date=target_date,
                time=datetime.strptime(f'{8 + (i % 16):02d}:{i % 60:02d}:00', '%H:%M:%S').time(),
                meal_name=f'Performance Test Meal {i}',
                grams=300 + i,
                water_ml=150 + i,
                meal_type_fresh=i % 2 == 0,
                meal_type_dry=i % 2 == 1,
                prep_method=PrepMethod.BOILED,
                body_condition=BodyConditionScale.IDEAL if i % 3 == 0 else BodyConditionScale.ABOVE_IDEAL
            )
            db_session.add(log)
        db_session.commit()
        
        # Test response time
        start_time = time.time()
        response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'per_page': 50
            }
        )
        end_time = time.time()
        
        assert response.status_code == 200
        assert end_time - start_time < 5.0  # Should respond within 5 seconds
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'kpis' in data
        assert 'pagination' in data

    def test_multi_project_data_isolation(self, authenticated_client, test_user, db_session):
        """Test that data is properly isolated between projects"""
        from k9.models.models import Project, Dog, FeedingLog, PrepMethod, BodyConditionScale, DogGender
        from datetime import datetime
        
        # Create second project
        project2 = Project(
            name='Second Test Project',
            code='TP002',
            description='Second test project',
            start_date=date.today() - timedelta(days=10),
            manager_id=test_user.id
        )
        db_session.add(project2)
        db_session.commit()
        
        # Create dog for second project
        dog2 = Dog(
            code='K9-999',
            name='Isolated Dog',
            breed='Labrador',
            birth_date=date(2021, 1, 1),
            gender=DogGender.FEMALE
        )
        db_session.add(dog2)
        db_session.commit()
        
        # Create feeding log for second project
        target_date = date.today()
        log2 = FeedingLog(
            project_id=project2.id,
            dog_id=dog2.id,
            date=target_date,
            time=datetime.strptime('12:00:00', '%H:%M:%S').time(),
            meal_name='Isolated Meal',
            grams=999,
            water_ml=999,
            meal_type_fresh=True,
            meal_type_dry=False,
            prep_method=PrepMethod.STEAMED,
            body_condition=BodyConditionScale.IDEAL
        )
        db_session.add(log2)
        db_session.commit()
        
        # Test that project2 data doesn't appear in project1 results
        response1 = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': self.test_project.id,  # Original project
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        
        if response1.status_code == 200:
            data1 = json.loads(response1.data)
            # Should not contain the isolated meal
            meal_names = [row['اسم_الوجبة'] for row in data1['rows']]
            assert 'Isolated Meal' not in meal_names

    def test_error_recovery_and_resilience(self, authenticated_client, test_project):
        """Test system resilience to various error conditions"""
        # Test with invalid date formats
        invalid_dates = ['invalid-date', '2023-13-01', '2023-02-30', '']
        
        for invalid_date in invalid_dates:
            response = authenticated_client.get(
                '/api/breeding/feeding-reports/daily',
                query_string={
                    'project_id': test_project.id,
                    'date': invalid_date
                }
            )
            # Should handle gracefully (400 error, not 500)
            assert response.status_code in [400, 422]
        
        # Test with invalid pagination parameters
        invalid_pages = [-1, 0, 'abc', '']
        for invalid_page in invalid_pages:
            response = authenticated_client.get(
                '/api/breeding/feeding-reports/daily',
                query_string={
                    'project_id': test_project.id,
                    'date': date.today().strftime('%Y-%m-%d'),
                    'page': invalid_page
                }
            )
            # Should handle gracefully
            assert response.status_code in [200, 400, 422]

    def test_sequential_access_patterns(self, authenticated_client, test_project, test_feeding_logs):
        """Test sequential access patterns to validate consistency"""
        target_date = date.today()
        
        # Make multiple sequential requests
        results = []
        for i in range(3):
            response = authenticated_client.get(
                '/api/breeding/feeding-reports/daily',
                query_string={
                    'project_id': test_project.id,
                    'date': target_date.strftime('%Y-%m-%d'),
                    'page': 1,
                    'per_page': 10
                }
            )
            results.append(response.status_code)
            
            if response.status_code == 200:
                data = json.loads(response.data)
                # Results should be consistent across requests
                assert data['success'] is True
                assert 'kpis' in data
        
        # All requests should return consistent results
        assert all(status == results[0] for status in results)

    def test_end_to_end_user_workflow(self, authenticated_client, test_feeding_logs, test_project, test_dogs):
        """Test complete end-to-end user workflow"""
        # Simulate real user behavior
        target_date = date.today()
        
        # 1. User navigates to daily report
        page_response = authenticated_client.get('/breeding/feeding-reports/daily')
        assert page_response.status_code == 200
        
        # 2. User selects project and date
        report_response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        assert report_response.status_code == 200
        
        # 3. System loads data via API
        api_response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d')
            }
        )
        assert api_response.status_code == 200
        data = json.loads(api_response.data)
        
        # 4. User filters by specific dog
        if test_dogs:
            filtered_response = authenticated_client.get(
                '/api/breeding/feeding-reports/daily',
                query_string={
                    'project_id': test_project.id,
                    'date': target_date.strftime('%Y-%m-%d'),
                    'dog_id': test_dogs[0].id
                }
            )
            assert filtered_response.status_code == 200
        
        # 5. User changes page size
        paginated_response = authenticated_client.get(
            '/api/breeding/feeding-reports/daily',
            query_string={
                'project_id': test_project.id,
                'date': target_date.strftime('%Y-%m-%d'),
                'per_page': 10
            }
        )
        assert paginated_response.status_code == 200
        paginated_data = json.loads(paginated_response.data)
        assert paginated_data['pagination']['per_page'] == 10