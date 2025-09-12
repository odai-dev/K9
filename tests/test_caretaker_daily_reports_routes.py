import pytest
from flask import url_for


@pytest.mark.unit
class TestCaretakerDailyReportsRoutes:
    """Test suite for caretaker daily reports route rendering and templates"""

    def test_caretaker_daily_report_page_renders(self, authenticated_client, test_project):
        """Test that caretaker daily report page renders successfully"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        assert b'<html' in response.data  # Basic HTML structure
        assert 'text/html' in response.headers.get('Content-Type', '')

    def test_rtl_template_elements(self, authenticated_client, test_project):
        """Test that templates contain RTL-specific elements"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for RTL direction
        assert 'dir="rtl"' in content or 'direction: rtl' in content
        
        # Check for Arabic content related to caretaker reports
        assert any(arabic_char in content for arabic_char in 'تقريرالرعايةاليومية')
        
        # Check for Bootstrap RTL
        assert 'bootstrap.rtl' in content or 'rtl' in content.lower()

    def test_arabic_labels_present(self, authenticated_client, test_project):
        """Test that Arabic labels are present in templates"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for key Arabic labels specific to caretaker reports
        arabic_terms = [
            'تقرير الرعاية اليومية',
            'المشروع',
            'التاريخ',
            'الكلب',
            'تنظيف البيت',
            'تنظيف الكلب',
            'القائم بالرعاية',
            'مهام رعاية الكلب',
            'مهام تنظيف البيت',
            'ملاحظات'
        ]
        
        # At least some Arabic terms should be present
        arabic_found = sum(1 for term in arabic_terms if term in content)
        assert arabic_found > 3  # At least 3 Arabic terms should be found

    def test_javascript_functionality_included(self, authenticated_client, test_project):
        """Test that JavaScript functionality is included in templates"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for JavaScript elements
        assert '<script' in content
        
        # Check for caretaker-specific JavaScript file
        assert 'reports_caretaker_daily.js' in content
        
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
            '/reports/breeding/caretaker-daily/',
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

    def test_specialized_table_headers_present(self, authenticated_client, test_project):
        """Test that caretaker daily report includes proper 2-row header table structure"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for 2-row header structure (rowspan and colspan)
        assert 'rowspan="2"' in content
        assert 'colspan="4"' in content
        
        # Check for grouped column headers
        assert 'مهام رعاية الكلب' in content      # Dog grooming group
        assert 'مهام تنظيف البيت' in content      # House cleaning group
        
        # Check for individual task headers
        cleaning_task_headers = [
            'تنظيف الكلب',         # Dog cleaning
            'استحمام الكلب',       # Dog washing
            'تمشيط الكلب',         # Dog brushing
            'تنظيف الأواني',       # Bowl/bucket cleaning
            'تنظيف البيت',         # House cleaning
            'شفط البيت',           # House vacuuming
            'تنظيف الصنبور',       # Tap cleaning
            'تنظيف البالوعة'       # Drain cleaning
        ]
        
        for header in cleaning_task_headers:
            assert header in content, f"Missing cleaning task header: {header}"

    def test_form_elements_present(self, authenticated_client, test_project):
        """Test that form elements for filters are present"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
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

    def test_unified_filters_present(self, authenticated_client, test_project):
        """Test that unified filters are included in the template"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for unified filters inclusion
        assert 'unified-filters' in content
        
        # Check for range type selector
        range_types = ['daily', 'weekly', 'monthly', 'custom']
        range_found = sum(1 for range_type in range_types if range_type in content)
        assert range_found > 2

    def test_kpi_cards_structure(self, authenticated_client, test_project):
        """Test that KPI cards are properly structured for caretaker activities"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for card structure
        assert 'card' in content  # Bootstrap cards
        assert 'kpi' in content.lower() or 'مؤشر' in content
        
        # Check for caretaker-specific KPI displays
        kpi_elements = [
            'id="total-entries"',        # Total entries KPI
            'id="unique-dogs"',          # Unique dogs KPI
            'id="house-clean-count"',    # House cleaning count
            'id="dog-clean-count"',      # Dog cleaning count
            'id="full-clean-count"',     # Full cleaning count
            'id="date-range-display"'    # Date range display
        ]
        
        kpi_found = sum(1 for element in kpi_elements if element in content)
        assert kpi_found > 3

    def test_export_functionality_present(self, authenticated_client, test_project):
        """Test that export functionality is available"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for export form
        assert 'id="pdf-export-form"' in content
        
        # Check for export buttons/functionality
        export_elements = [
            'export',
            'pdf',
            'تصدير',  # Export in Arabic
            'طباعة'   # Print in Arabic
        ]
        
        export_found = sum(1 for element in export_elements if element.lower() in content.lower())
        assert export_found > 0

    def test_export_form_fields_present(self, authenticated_client, test_project):
        """Test that export form includes necessary fields"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for export form fields
        export_form_fields = [
            'id="export-range-type"',
            'id="export-project-id"',
            'id="export-dog-id"',
            'id="export-date"',
            'id="export-week-start"',
            'id="export-year-month"',
            'id="export-date-from"',
            'id="export-date-to"'
        ]
        
        for field in export_form_fields:
            assert field in content, f"Missing export form field: {field}"

    def test_pagination_controls_present(self, authenticated_client, test_project):
        """Test that pagination controls are included"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
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

    def test_loading_states_present(self, authenticated_client, test_project):
        """Test that loading and empty states are included"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for loading state
        assert 'id="table-loading"' in content
        assert 'جاري تحميل البيانات' in content  # Loading data message
        
        # Check for empty state
        assert 'id="empty-state"' in content
        assert 'لا توجد بيانات' in content  # No data message

    def test_responsive_design_classes(self, authenticated_client, test_project):
        """Test that responsive design classes are present"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
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
            'd-block',
            'btn-group',        # For pagination buttons
            'justify-content-between'  # For header layout
        ]
        
        responsive_found = sum(1 for cls in responsive_classes if cls in content)
        assert responsive_found > 4

    def test_error_handling_in_templates(self, authenticated_client):
        """Test that templates handle missing parameters gracefully"""
        # Test without project_id parameter
        response = authenticated_client.get('/reports/breeding/caretaker-daily/')
        
        # Should render template with error message or redirect, not crash
        assert response.status_code in [200, 400, 422]  # Various acceptable responses
        
        if response.status_code == 200:
            content = response.data.decode('utf-8')
            assert '<html' in content  # Should still be valid HTML

    def test_navigation_integration(self, authenticated_client, test_project):
        """Test that caretaker reports are properly integrated in navigation"""
        # Get a page that should have the main navigation
        response = authenticated_client.get('/reports/breeding/caretaker-daily/', 
                                          query_string={'project_id': test_project.id})
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for navigation elements
        nav_elements = [
            'nav',
            'navbar',
            'تقارير',    # Reports in Arabic
            'الرعاية'    # Caretaker in Arabic
        ]
        
        nav_found = sum(1 for element in nav_elements if element in content)
        assert nav_found > 1

    def test_page_title_and_heading(self, authenticated_client, test_project):
        """Test that page has correct title and headings"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for page title in head
        assert '<title>' in content and 'تقرير الرعاية اليومية' in content
        
        # Check for main heading
        assert 'تقرير الرعاية اليومية' in content
        
        # Check for breadcrumb or back navigation
        assert 'العودة للوحة التحكم' in content or 'dashboard' in content.lower()

    def test_template_extends_base(self, authenticated_client, test_project):
        """Test that template properly extends base template"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Should have HTML structure from base template
        assert '<!DOCTYPE html>' in content or '<html' in content
        assert '<head>' in content
        assert '<body>' in content
        
        # Should include CSS and JS from base
        assert 'bootstrap' in content.lower()
        assert 'style.css' in content or 'stylesheet' in content

    def test_accessibility_features(self, authenticated_client, test_project):
        """Test that template includes accessibility features"""
        response = authenticated_client.get(
            '/reports/breeding/caretaker-daily/',
            query_string={'project_id': test_project.id}
        )
        
        assert response.status_code == 200
        content = response.data.decode('utf-8')
        
        # Check for accessibility attributes
        accessibility_features = [
            'aria-label',
            'role=',
            'alt=',
            'lang=',
            'tabindex'
        ]
        
        accessibility_found = sum(1 for feature in accessibility_features if feature in content)
        assert accessibility_found > 1  # Should have some accessibility features