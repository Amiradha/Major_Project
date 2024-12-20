from datetime import datetime

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_GET
from django.db.models import Q, Avg, Count
from django.db.models.functions import ExtractYear

from .models import (
    ProgramMaster,
    CourseEvaluationComponent,
    StudentMarks,
    StudentMarksSummary,
    User,
)
from .forms import LoginForm
from .decorators import login_required


@login_required
@require_GET
def get_years(request):
    """
    Get available academic years for a given program
    """
    program = request.GET.get('program', '')
    
    try:
        # Get program ID
        program_obj = ProgramMaster.objects.get(
            program_name=program, 
            active='Y'
        )

        # Get years
        years_query = StudentMarksSummary.objects.filter(
            program_course_key__startswith=program_obj.program_id
        ).annotate(
            year=ExtractYear('semester_start_date')
        ).values_list('year', flat=True).distinct()
        
        years = sorted(list(years_query))
        
        return JsonResponse({
            'years': years,
            'status': 'success'
        })
    
    except ProgramMaster.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid program',
            'status': 'error'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)

@login_required
@require_GET
def get_courses(request):
    """
    Get available courses for a given program and year
    """
    program = request.GET.get('program', '')
    year = request.GET.get('year', '')
    
    try:
        # Get program ID
        program_obj = ProgramMaster.objects.get(
            program_name=program, 
            active='Y'
        )

        # Get courses
        courses_query = StudentMarksSummary.objects.filter(
            program_course_key__startswith=program_obj.program_id,
            semester_start_date__year=year
        ).values_list('course_code', flat=True).distinct()
        
        courses = list(courses_query)
        
        return JsonResponse({
            'courses': courses,
            'status': 'success'
        })
    
    except ProgramMaster.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid program',
            'status': 'error'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)

@login_required
@require_GET
def get_components(request):
    """
    Get available evaluation components for a given program and course
    """
    program = request.GET.get('program', '')
    course = request.GET.get('course', '')
    
    try:
        # Get program ID
        program_obj = ProgramMaster.objects.get(
            program_name=program, 
            active='Y'
        )

        # Get evaluation components
        components_query = CourseEvaluationComponent.objects.filter(
            course_code=course,
            program_id=program_obj.program_id
        ).values_list('evaluation_id_name', flat=True).distinct()
        
        components = list(components_query)
        
        return JsonResponse({
            'components': components,
            'status': 'success'
        })
    
    except ProgramMaster.DoesNotExist:
        return JsonResponse({
            'error': 'Invalid program',
            'status': 'error'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': str(e),
            'status': 'error'
        }, status=500)


    
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(username=username, password=password)
                request.session['user_id'] = user.id  # Store user ID in session
                return redirect('academic:component_performance')  # Redirect to the component performance page
            except User.DoesNotExist:
                messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()
    return render(request, 'academic/login.html', {'form': form})

def logout_view(request):
    request.session.flush()  # Clear the session
    return redirect('academic:login')  # Redirect to login page
@login_required
def course_performance(request):
    # Get unique academic years and course codes for the filter
    academic_years = StudentMarksSummary.objects.dates('semester_start_date', 'year')
    course_codes = StudentMarksSummary.objects.values_list('course_code', flat=True).distinct()
    
    selected_year = request.GET.get('year')
    selected_course = request.GET.get('course')
    
    context = {
        'academic_years': academic_years,
        'course_codes': course_codes,
        'selected_year': selected_year,
        'selected_course': selected_course,
    }
    
    return render(request, 'academic/course_performance.html', context)

@login_required
def component_performance(request):
    try:
        # Predefined evaluation components
        all_components = ['CT1', 'CT2', 'DA1', 'DA2', 'EXT', 'REM', 'ATT', 'AA']

        # Get filter parameters from request
        selected_program = request.GET.get('program', '')
        selected_year = request.GET.get('year', '')
        selected_course = request.GET.get('course_code', '')
        selected_components = request.GET.getlist('evaluation_components')

        # Base context setup
        context = {
            'programs': ProgramMaster.objects.filter(
                Q(program_name__icontains='B.TECH') & 
                Q(active='Y')
            ).values_list('program_name', flat=True).distinct(),
            'selected_program': selected_program,
            'years': [],
            'courses': [],
            'selected_year': selected_year,
            'selected_course': selected_course,
            'all_components': all_components,
            'selected_components': selected_components,
            'evaluation_components': all_components,  # Make all components available for selection
        }

        if not selected_program:
            return render(request, 'academic/component_performance.html', context)

        # Program validation and retrieval
        try:
            program_obj = ProgramMaster.objects.get(
                program_name=selected_program, 
                active='Y'
            )
        except ProgramMaster.DoesNotExist:
            context['error_message'] = "Invalid program selected."
            return render(request, 'academic/component_performance.html', context)

        # Get years
        years_query = StudentMarksSummary.objects.filter(
            program_course_key__startswith=program_obj.program_id
        ).annotate(
            year=ExtractYear('semester_start_date')
        ).values_list('year', flat=True).distinct()
        
        context['years'] = sorted(list(years_query))

        if not selected_year:
            return render(request, 'academic/component_performance.html', context)

        # Year validation
        try:
            selected_year = int(selected_year)
            if selected_year not in context['years']:
                context['error_message'] = "Invalid year selected."
                return render(request, 'academic/component_performance.html', context)
        except (ValueError, TypeError):
            context['error_message'] = "Invalid year format."
            return render(request, 'academic/component_performance.html', context)

        # Get courses
        courses_query = StudentMarksSummary.objects.filter(
            program_course_key__startswith=program_obj.program_id,
            semester_start_date__year=selected_year
        ).values_list('course_code', flat=True).distinct()
        
        context['courses'] = list(courses_query)

        if not selected_course or not selected_components:
            return render(request, 'academic/component_performance.html', context)

        # Course validation
        if selected_course not in context['courses']:
            context['error_message'] = "Invalid course selected."
            return render(request, 'academic/component_performance.html', context)

        # Fetch and process component data
        evaluation_components = CourseEvaluationComponent.objects.filter(
            course_code=selected_course,
            program_id=program_obj.program_id,
            evaluation_id_name__in=selected_components
        ).values('evaluation_id', 'evaluation_id_name', 'maximum_marks')

        # Calculate performance metrics for selected components
        component_performance = {}
        for component in evaluation_components:
            avg_marks = StudentMarks.objects.filter(
                evaluation_id=component['evaluation_id'],
                course_code=selected_course,
                program_course_key__startswith=program_obj.program_id
            ).aggregate(Avg('marks'))['marks__avg'] or 0
            
            component_performance[component['evaluation_id_name']] = round(avg_marks, 2)

        # Prepare chart data
        context['component_performance'] = {
            'labels': list(component_performance.keys()),
            'data': list(component_performance.values())
        }

        # Calculate grade distribution for the course
        grade_distribution = StudentMarksSummary.objects.filter(
            course_code=selected_course,
            semester_start_date__year=selected_year,
            program_course_key__startswith=program_obj.program_id
        ).values('internal_grade').annotate(
            count=Count('roll_number')
        ).filter(internal_grade__isnull=False)

        # Prepare grade distribution data
        context['grade_distribution'] = {
            'labels': [grade['internal_grade'] for grade in grade_distribution],
            'data': [grade['count'] for grade in grade_distribution]
        }

        # Add summary statistics
        context.update({
            'total_students': StudentMarksSummary.objects.filter(
                course_code=selected_course,
                semester_start_date__year=selected_year,
                program_course_key__startswith=program_obj.program_id
            ).count(),
            'course_details': {
                'course_code': selected_course,
                'program_name': selected_program,
                'academic_year': selected_year
            }
        })
        # Get unique roll numbers first
        unique_roll_numbers = StudentMarks.objects.filter(
            evaluation_id__in=[component['evaluation_id'] for component in evaluation_components],
            course_code=selected_course,
            program_course_key__startswith=program_obj.program_id
        ).values_list('roll_number', flat=True).distinct().order_by('roll_number')

        # Initialize datasets for each component
        component_datasets = {}
        for component in evaluation_components:
            marks_data = StudentMarks.objects.filter(
                evaluation_id=component['evaluation_id'],
                course_code=selected_course,
                program_course_key__startswith=program_obj.program_id
            ).order_by('roll_number').values('roll_number', 'marks')
            
            # Create a dictionary mapping roll numbers to marks
            marks_dict = {entry['roll_number']: entry['marks'] for entry in marks_data}
            
            # Ensure we have data for all roll numbers (use 0 for missing data)
            component_marks = [marks_dict.get(roll_number, 0) for roll_number in unique_roll_numbers]
            
            component_datasets[component['evaluation_id_name']] = component_marks

        # Prepare the line chart data structure
        context['line_chart_data'] = {
            'roll_numbers': list(unique_roll_numbers),
            'datasets': [{
                'label': component_name,
                'data': marks_list
            } for component_name, marks_list in component_datasets.items()]
        }

        scatter_datasets = []
        for component_name, marks_list in component_datasets.items():
            scatter_data = [
                {'x': str(roll_number), 'y': marks} 
                for roll_number, marks in zip(unique_roll_numbers, marks_list) 
                if marks > 0
            ]
            scatter_datasets.append({
            'label': component_name,
            'data': scatter_data
            })

        context['scatter_chart_data'] = {
    'datasets': scatter_datasets
}

        return render(request, 'academic/component_performance.html', context)

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in component_performance: {str(e)}", exc_info=True)
        
        context = {
            'error_message': f'An unexpected error occurred: {str(e)}',
            'programs': ProgramMaster.objects.filter(
                Q(program_name__icontains='B.TECH') & 
                Q(active='Y')
            ).values_list('program_name', flat=True).distinct(),
        }
        return render(request, 'academic/component_performance.html', context)
    
@login_required

def academic_results(request):
    try:
        # Get filter parameters from request
        selected_program = request.GET.get('program', '')
        selected_year = request.GET.get('year', '')
        selected_course = request.GET.get('course_code', '')

        # Step 1: Get unique programs
        programs = ProgramMaster.objects.filter(
            Q(program_name__icontains='B.TECH') & 
            Q(active='Y')
        ).values_list('program_name', flat=True).distinct()

        # Initialize context with programs
        context = {
            'programs': programs,
            'selected_program': selected_program,
            'years': [],
            'courses': [],
        }

        # If no program is selected, return initial page
        if not selected_program:
            return render(request, 'academic/results.html', context)

        # Step 2: Get available years for selected program
        years_query = StudentMarksSummary.objects.filter(
            program_course_key__startswith=ProgramMaster.objects.get(program_name=selected_program).program_id
        ).annotate(year=ExtractYear('semester_start_date')).values_list('year', flat=True).distinct()
        
        context['years'] = sorted(list(years_query))
        context['selected_year'] = selected_year

        # If no year is selected, return page with years
        if not selected_year:
            return render(request, 'academic/results.html', context)

        # Step 3: Get available courses for selected program and year
        courses_query = StudentMarksSummary.objects.filter(
            program_course_key__startswith=ProgramMaster.objects.get(program_name=selected_program).program_id,
            semester_start_date__year=selected_year
        ).values_list('course_code', flat=True).distinct()
        
        context['courses'] = list(courses_query)
        context['selected_course'] = selected_course

        # If no course is selected, return page with courses
        if not selected_course:
            return render(request, 'academic/results.html', context)

        # Final Step: Fetch and process results
        # Get program details
        program_details = ProgramMaster.objects.get(program_name=selected_program)

        # Get evaluation components
        evaluation_components = CourseEvaluationComponent.objects.filter(
            course_code=selected_course,
            program_id=program_details.program_id
        ).values(
            'evaluation_id', 'evaluation_id_name',
            'maximum_marks', 'component_full_name'
        )

        # Get individual marks
        marks_data = StudentMarks.objects.filter(
            course_code=selected_course,
            semester_start_date__year=selected_year,
            program_course_key__startswith=program_details.program_id
        ).values(
            'roll_number', 'evaluation_id', 'marks',
            'program_course_key', 'semester_start_date', 'semester_end_date'
        )

        # Get marks summary
        summary_data = StudentMarksSummary.objects.filter(
            course_code=selected_course,
            semester_start_date__year=selected_year,
            program_course_key__startswith=program_details.program_id
        ).values(
            'roll_number', 'total_internal', 'total_external', 
            'total_marks', 'internal_grade', 'earned_credits',
            'program_course_key', 'semester_start_date', 'semester_end_date'
        )

        # Combine the data
        consolidated_data = []
        for summary in summary_data:
            # Get student's individual evaluation marks
            student_marks = {
                mark['evaluation_id']: mark['marks']
                for mark in marks_data
                if mark['roll_number'] == summary['roll_number']
            }
            
            # Prepare evaluation details
            evaluation_details = []
            for comp in evaluation_components:
                evaluation_details.append({
                    'evaluation_id': comp['evaluation_id'],
                    'evaluation_name': comp['evaluation_id_name'],
                    'maximum_marks': comp['maximum_marks'],
                    'marks_obtained': student_marks.get(comp['evaluation_id'])
                })
            
            consolidated_data.append({
                'program_name': selected_program,
                'program_type': 'Full-Time' if program_details.program_type == 'F' else 'Part-Time',
                'course_code': selected_course,
                'roll_number': summary['roll_number'],
                'internal_marks': summary['total_internal'],
                'external_marks': summary['total_external'],
                'total_marks': summary['total_marks'],
                'grades': summary['internal_grade'],
                'credits_earned': summary['earned_credits'],
                'semester_start': summary['semester_start_date'],
                'semester_end': summary['semester_end_date'],
                'evaluation_details': evaluation_details
            })

        # Update context with final results
        context.update({
            'consolidated_data': consolidated_data,
            'total_students': len(consolidated_data),
        })

        return render(request, 'academic/results.html', context)

    except Exception as e:
        # Log the error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error in academic_results: {str(e)}")

        # Return error response
        return render(request, 'academic/results.html', {
            'error_message': f'An error occurred: {str(e)}',
            'programs': ProgramMaster.objects.filter(
                Q(program_name__icontains='B.TECH') & 
                Q(active='Y')
            ).values_list('program_name', flat=True).distinct(),
        })