"""Celery tasks for schedule module."""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta, date
from .models import TimetableTemplate
from .services import LessonGenerator
import logging

logger = logging.getLogger(__name__)


@shared_task(name='schedule.generate_weekly_lessons')
def generate_weekly_lessons():
    """
    Generate lessons for the upcoming week for all active timetables.
    
    This task should run weekly (e.g., every Sunday evening).
    Generates lessons for the next 7 days.
    """
    logger.info("Starting weekly lesson generation task")
    
    # Get all active timetables
    active_timetables = TimetableTemplate.objects.filter(
        is_active=True,
        deleted_at__isnull=True
    ).select_related('branch', 'academic_year')
    
    total_created = 0
    total_skipped = 0
    processed_count = 0
    error_count = 0
    
    today = timezone.now().date()
    # Generate for next week (7 days ahead)
    start_date = today + timedelta(days=1)
    end_date = start_date + timedelta(days=6)
    
    for timetable in active_timetables:
        try:
            logger.info(
                f"Generating lessons for timetable: {timetable.name} "
                f"(Branch: {timetable.branch.name})"
            )
            
            created, skipped = LessonGenerator.generate_lessons_for_period(
                timetable=timetable,
                start_date=start_date,
                end_date=end_date,
                skip_existing=True
            )
            
            total_created += created
            total_skipped += skipped
            processed_count += 1
            
            logger.info(
                f"Generated {created} lessons, skipped {skipped} for {timetable.name}"
            )
            
        except Exception as e:
            error_count += 1
            logger.error(
                f"Error generating lessons for timetable {timetable.id}: {str(e)}",
                exc_info=True
            )
    
    logger.info(
        f"Weekly lesson generation completed. "
        f"Processed: {processed_count}, Created: {total_created}, "
        f"Skipped: {total_skipped}, Errors: {error_count}"
    )
    
    return {
        'processed_count': processed_count,
        'total_created': total_created,
        'total_skipped': total_skipped,
        'error_count': error_count,
        'start_date': str(start_date),
        'end_date': str(end_date)
    }


@shared_task(name='schedule.generate_monthly_lessons')
def generate_monthly_lessons():
    """
    Generate lessons for the upcoming month for all active timetables.
    
    This task should run monthly (e.g., on the 1st of each month).
    Generates lessons for the entire upcoming month.
    """
    logger.info("Starting monthly lesson generation task")
    
    # Get all active timetables
    active_timetables = TimetableTemplate.objects.filter(
        is_active=True,
        deleted_at__isnull=True
    ).select_related('branch', 'academic_year')
    
    total_created = 0
    total_skipped = 0
    processed_count = 0
    error_count = 0
    
    today = timezone.now().date()
    # Calculate next month
    if today.month == 12:
        year = today.year + 1
        month = 1
    else:
        year = today.year
        month = today.month + 1
    
    for timetable in active_timetables:
        try:
            logger.info(
                f"Generating monthly lessons for timetable: {timetable.name} "
                f"(Branch: {timetable.branch.name})"
            )
            
            created, skipped = LessonGenerator.generate_lessons_for_month(
                timetable=timetable,
                year=year,
                month=month
            )
            
            total_created += created
            total_skipped += skipped
            processed_count += 1
            
            logger.info(
                f"Generated {created} lessons, skipped {skipped} for {timetable.name}"
            )
            
        except Exception as e:
            error_count += 1
            logger.error(
                f"Error generating monthly lessons for timetable {timetable.id}: {str(e)}",
                exc_info=True
            )
    
    logger.info(
        f"Monthly lesson generation completed. "
        f"Processed: {processed_count}, Created: {total_created}, "
        f"Skipped: {total_skipped}, Errors: {error_count}"
    )
    
    return {
        'processed_count': processed_count,
        'total_created': total_created,
        'total_skipped': total_skipped,
        'error_count': error_count,
        'year': year,
        'month': month
    }


@shared_task(name='schedule.generate_quarter_lessons')
def generate_quarter_lessons(timetable_id, quarter_id):
    """
    Generate lessons for an entire quarter.
    
    Args:
        timetable_id: UUID of the timetable template
        quarter_id: UUID of the quarter
    
    Returns:
        dict with generation results
    """
    logger.info(f"Generating lessons for quarter {quarter_id} using timetable {timetable_id}")
    
    try:
        from apps.school.academic.models import Quarter
        
        timetable = TimetableTemplate.objects.get(id=timetable_id)
        quarter = Quarter.objects.get(id=quarter_id)
        
        created, skipped = LessonGenerator.generate_lessons_for_quarter(
            timetable=timetable,
            quarter=quarter
        )
        
        logger.info(
            f"Generated {created} lessons, skipped {skipped} "
            f"for quarter {quarter.name}"
        )
        
        return {
            'success': True,
            'created_count': created,
            'skipped_count': skipped,
            'quarter_name': quarter.name,
            'timetable_name': timetable.name
        }
        
    except Exception as e:
        logger.error(
            f"Error generating quarter lessons: {str(e)}",
            exc_info=True
        )
        return {
            'success': False,
            'error': str(e)
        }
