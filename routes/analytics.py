from flask import Blueprint, jsonify, request
from models import db
from models.project import Project
from datetime import datetime, timedelta 
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from sqlalchemy import func, text
from models.user import User
import json
import pytz

analytics = Blueprint('analytics', __name__)

def get_mountain_time():
    mountain = pytz.timezone('America/Denver')
    return datetime.now(mountain)

def get_region_stats(region, start_date=None, end_date=None):
    try:
        print(f"\n=== Getting stats for {region} region ===")
        print(f"Start date: {start_date}")
        print(f"End date: {end_date}")
        
        # Base query
        query = Project.query.filter(Project.region == region)
        print(f"Base query SQL: {query}")
        
        if start_date and end_date:
            # Convert string dates to datetime if they aren't already
            if isinstance(start_date, str):
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            if isinstance(end_date, str):
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            
            print(f"Filtering by date range: {start_date} to {end_date}")
            # Convert project.date to the same date as start_date for comparison
            query = query.filter(
                func.date(Project.date) == func.date(start_date)
            ) if start_date.date() == end_date.date() else query.filter(
                Project.date >= start_date,
                Project.date <= end_date
            )
            print(f"Filtered query SQL: {query}")
        
        # Execute query and get all projects
        projects = query.all()
        print(f"Found {len(projects)} projects for {region}")
        
        # Debug: Print each project's details
        for project in projects:
            print(f"\nProject {project.id}:")
            print(f"  Date: {project.date}")
            print(f"  Work Type: {project.work_type}")
            print(f"  Job Cost Type: {project.job_cost_type}")
        
        # Initialize counters
        work_types = {}
        job_cost_types = {}
        
        # Process each project
        for project in projects:
            print(f"\nProcessing project {project.id}:")
            print(f"  Date: {project.date}")
            print(f"  Work Type: {project.work_type}")
            print(f"  Job Cost Type: {project.job_cost_type}")
            
            # Process work types
            if project.work_type:
                types = [t.strip() for t in project.work_type.split(',') if t.strip()]
                print(f"  Parsed Work Types: {types}")
                for wt in types:
                    work_types[wt] = work_types.get(wt, 0) + 1
            
            # Process job cost types
            if project.job_cost_type:
                types = [t.strip() for t in project.job_cost_type.split(',') if t.strip()]
                print(f"  Parsed Job Cost Types: {types}")
                for jct in types:
                    job_cost_types[jct] = job_cost_types.get(jct, 0) + 1
        
        print(f"\nFinal counts for {region}:")
        print(f"Work type counts: {work_types}")
        print(f"Job cost type counts: {job_cost_types}")
        
        # Format the results
        result = {
            'work_type': {
                'labels': list(work_types.keys()),
                'values': list(work_types.values())
            },
            'job_cost_type': {
                'labels': list(job_cost_types.keys()),
                'values': list(job_cost_types.values())
            }
        }
        
        print(f"Returning data for {region}: {result}")
        return result
        
    except Exception as e:
        print(f"Error in get_region_stats for {region}: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return {
            'work_type': {'labels': [], 'values': []},
            'job_cost_type': {'labels': [], 'values': []}
        }

@analytics.route('/data', methods=['GET'])
def get_analytics_data():
    try:
        print("\n=== Starting Analytics Data Request ===")
        
        time_frame = request.args.get('timeFrame', 'month')
        print(f"Requested time frame: {time_frame}")
        
        # Calculate date range using Mountain Time
        end_date = get_mountain_time()
        if time_frame == 'today':
            start_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)
        elif time_frame == 'week':
            start_date = end_date - timedelta(weeks=1)
        elif time_frame == 'year':
            start_date = end_date - timedelta(days=365)
        else:  # default to month
            start_date = end_date - timedelta(days=30)
            
        # Set time to start of day for start_date and end of day for end_date
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
        print(f"Date range: {start_date} to {end_date}")
        
        # Get stats for both regions
        north_stats = get_region_stats('North', start_date, end_date)
        south_stats = get_region_stats('South', start_date, end_date)
        
        # Combine results
        result = {
            'north': north_stats,
            'south': south_stats
        }
        
        print("\nFinal response data:")
        print(json.dumps(result, indent=2))
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error in get_analytics_data: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@analytics.route('/monthly', methods=['GET'])
def get_monthly_analytics():
    try:
        print(f"\n=== Starting Monthly Analytics ===")
        
        # Calculate date range for the past month
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Set time to start of day for start_date and end of day for end_date
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        print(f"\nFiltering projects between {start_date} and {end_date}")
        
        # Get stats for both regions
        print("\nGetting North region stats...")
        north_stats = get_region_stats('North', start_date, end_date)
        
        print("\nGetting South region stats...")
        south_stats = get_region_stats('South', start_date, end_date)
        
        result = {
            'north': north_stats,
            'south': south_stats
        }
        
        print("\nFinal Response Data:")
        print(f"North Region:")
        print(f"  Work Types: {len(north_stats['work_type']['labels'])} types")
        print(f"  Job Cost Types: {len(north_stats['job_cost_type']['labels'])} types")
        print(f"South Region:")
        print(f"  Work Types: {len(south_stats['work_type']['labels'])} types")
        print(f"  Job Cost Types: {len(south_stats['job_cost_type']['labels'])} types")
        print("\n=== Monthly Analytics Complete ===")
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error generating analytics: {str(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            'error': 'Failed to generate analytics',
            'msg': str(e)
        }), 500 