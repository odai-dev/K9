import pytest
from flask import url_for


@pytest.mark.unit
class TestFeedingReportsRoutes:
    """Test suite for feeding reports route rendering and templates"""

    def test_daily_feeding_route_renders(self, authenticated_client, test_project):
        """Test that daily feeding report route renders successfully"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        assert b'<html' in response.data  # Basic HTML structure
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_weekly_feeding_route_renders(self, authenticated_client, test_project):
        """Test that weekly feeding report route renders successfully"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/weekly',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        assert b'<html' in response.data
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_rtl_template_elements(self, authenticated_client, test_project):
        """Test that templates contain RTL-specific elements"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for RTL direction
        assert 'dir="rtl"' in content or 'direction: rtl' in content
        
        # Check for Arabic content
        assert any(arabic_char in content for arabic_char in 'تقريراليوميالأسبوعيالتغذية')
        
        # Check for Bootstrap RTL
        assert 'bootstrap.rtl' in content or 'rtl' in content.lower()

    def test_arabic_labels_present(self, authenticated_client, test_project):
        """Test that Arabic labels are present in templates"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for key Arabic labels
        arabic_terms = [
            'تقرير التغذية اليومي',
            'المشروع',
            'التاريخ',
            'الكلب',
            'نوع الوجبة',
            'كمية الوجبة',
            'ماء الشرب',
            'ملاحظات'
        ]
        
        # At least some Arabic terms should be present
        arabic_found = sum(1 for term in arabic_terms if term in content)
        assert arabic_found > 3  # At least 3 Arabic terms should be found

    def test_javascript_functionality_included(self, authenticated_client, test_project):
        """Test that JavaScript functionality is included in templates"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for JavaScript elements
        assert '<script' in content
        
        # Check for key functionality
        js_features = [
            'loadData',
            'exportPDF',
            'pagination',
            'filters'
        ]
        
        # Should have some JavaScript functionality
        js_found = sum(1 for feature in js_features if feature in content)
        assert js_found > 0

    def test_table_structure_present(self, authenticated_client, test_project):
        """Test that table structures are present in templates"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for table elements
        assert '<table' in content
        assert '<thead' in content
        assert '<tbody' in content
        
        # Check for Bootstrap table classes
        assert 'table' in content
        assert 'table-striped' in content or 'table-bordered' in content

    def test_form_elements_present(self, authenticated_client, test_project):
        """Test that form elements for filters are present"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for form elements
        form_elements = [
            '<form',
            '<select',
            '<input',
            'type="date"',
            'project_id',
            'dog_id'
        ]
        
        form_found = sum(1 for element in form_elements if element in content)
        assert form_found > 3  # Should have most form elements

    def test_kpi_cards_structure(self, authenticated_client, test_project):
        """Test that KPI cards are properly structured"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for card structure
        assert 'card' in content  # Bootstrap cards
        assert 'kpi' in content.lower() or 'مؤشر' in content
        
        # Check for metric displays
        metrics = [
            'total-meals',
            'total-dogs',
            'total-quantity',
            'poor-conditions'
        ]
        
        metric_found = sum(1 for metric in metrics if metric in content)
        assert metric_found > 1

    def test_pagination_controls_present(self, authenticated_client, test_project):
        """Test that pagination controls are included"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for pagination elements
        pagination_elements = [
            'pagination',
            'page-link',
            'السابق',  # Previous in Arabic
            'التالي'   # Next in Arabic
        ]
        
        pagination_found = sum(1 for element in pagination_elements if element in content)
        assert pagination_found > 1

    def test_export_functionality_present(self, authenticated_client, test_project):
        """Test that export functionality is available"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for export buttons/functionality
        export_elements = [
            'export',
            'pdf',
            'تصدير',  # Export in Arabic
            'طباعة'   # Print in Arabic
        ]
        
        export_found = sum(1 for element in export_elements if element.lower() in content.lower())
        assert export_found > 0

    def test_responsive_design_classes(self, authenticated_client, test_project):
        """Test that responsive design classes are present"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/daily',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for responsive classes
        responsive_classes = [
            'col-',
            'row',
            'container',
            'table-responsive',
            'd-none',
            'd-block'
        ]
        
        responsive_found = sum(1 for cls in responsive_classes if cls in content)
        assert responsive_found > 3

    def test_weekly_report_specific_elements(self, authenticated_client, test_project):
        """Test weekly report specific template elements"""
        response = authenticated_client.get(
            '/breeding/feeding-reports/weekly',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for weekly-specific elements
        weekly_elements = [
            'الأسبوعي',  # Weekly in Arabic
            'week_start',
            'أسبوع',     # Week in Arabic
            'خلاصة'      # Summary in Arabic
        ]
        
        weekly_found = sum(1 for element in weekly_elements if element in content)
        assert weekly_found > 1

    def test_error_handling_in_templates(self, authenticated_client):
        """Test that templates handle missing parameters gracefully"""
        # Test without project_id parameter
        response = authenticated_client.get('/breeding/feeding-reports/daily')
        
        # Should render template with error message or redirect, not crash
        assert response.status_code in [200, 400, 422]  # Various acceptable responses
        
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            assert '<html' in content  # Should still be valid HTML

    def test_navigation_integration(self, authenticated_client, test_project):
        """Test that feeding reports are properly integrated in navigation"""
        # Get a page that should have the main navigation
        response = authenticated_client.get('/breeding/feeding-reports/daily', 
                                          query_string={'project_id': test_project.id})
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for navigation elements
        nav_elements = [
            'nav',
            'navbar',
            'تقارير',    # Reports in Arabic
            'التغذية'    # Feeding in Arabic
        ]
        
        nav_found = sum(1 for element in nav_elements if element in content)
        assert nav_found > 1