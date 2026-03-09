
# Create your views here.
from rest_framework.views import APIView,View
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
import logging
from django.shortcuts import render, redirect

from django.db import connection
from datetime import date
from typing import List, Dict, Optional


logger = logging.getLogger(__name__)

def dictfetchall(cursor):
    """Return all rows from a cursor as a dict"""
    columns = [col[0] for col in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def get_all_tasks() -> List[Dict]:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, description, due_date, status, created_at
            FROM tasks_task
            ORDER BY id DESC
        """)
        return dictfetchall(cursor)

def get_task_by_id(task_id: int) -> Optional[Dict]:
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, description, due_date, status, created_at
            FROM tasks_task WHERE id = %s
        """, [task_id])
        row = cursor.fetchone()
        if row:
            columns = [col[0] for col in cursor.description]
            print(dict(zip(columns, row)),"-----")
            return dict(zip(columns, row))
        return None

def create_task(title: str, description: str = "", due_date: Optional[str] = None, status: str = "pending") -> int:
    with connection.cursor() as cursor:
        cursor.execute("""
            INSERT INTO tasks_task (title, description, due_date, status)
            VALUES (%s, %s, %s, %s)
        """, [title, description, due_date, status])
        return cursor.lastrowid

def update_task(task_id: int, title: str, description: str, due_date: Optional[str], status: str) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("""
            UPDATE tasks_task
            SET title = %s, description = %s, due_date = %s, status = %s
            WHERE id = %s
        """, [title, description, due_date, status, task_id])
        return cursor.rowcount > 0

def delete_task(task_id: int) -> bool:
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM tasks_task WHERE id = %s", [task_id])
        return cursor.rowcount > 0

class TaskListCreateAPIView(APIView):
    def get(self, request):
        try:
            tasks = get_all_tasks()
            return Response(tasks)
        except Exception as e:
            logger.exception("Error fetching tasks")
            return Response({"error": "Internal server error"}, status=500)

    def post(self, request):
        try:
            data = request.data
            title = data.get("title", "").strip()
            if not title:
                raise ValidationError({"title": "This field is required."})

            task_id = create_task(
                title=title,
                description=data.get("description", ""),
                due_date=data.get("due_date"),
                status=data.get("status", "pending")
            )
            task = get_task_by_id(task_id)
            return Response(task, status=status.HTTP_201_CREATED)
        except ValidationError as e:
            return Response(e.detail, status=400)
        except Exception as e:
            logger.exception("Error creating task")
            return Response({"error": "Internal server error"}, status=500)


class TaskDetailAPIView(APIView):
    def get_object(self, pk):
        task = get_task_by_id(pk)
        if not task:
            raise NotFound(detail="Task not found")
        return task

    def get(self, request, pk):
        task = self.get_object(pk)
        return Response(task)

    def put(self, request, pk):
        data = request.data
        title = data.get("title", "").strip()
        if not title:
            raise ValidationError({"title": "This field is required."})

        updated = update_task(
            task_id=pk,
            title=title,
            description=data.get("description", ""),
            due_date=data.get("due_date"),
            status=data.get("status", "pending")
        )
        if not updated:
            raise NotFound(detail="Task not found")
        task = get_task_by_id(pk)
        return Response(task)

    def delete(self, request, pk):
        deleted = delete_task(pk)
        if not deleted:
            raise NotFound(detail="Task not found")
        return Response(status=status.HTTP_204_NO_CONTENT)

class TaskListView(View):
    def get(self, request):
        tasks = get_all_tasks()
        return render(request, 'tasks/task_list.html', {'tasks': tasks})

class TaskCreateView(View):
    def get(self, request):
        return render(request, 'tasks/task_form.html')

    def post(self, request):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date') or None
        status = request.POST.get('status', 'pending')

        if title:
            create_task(title, description, due_date, status)
        return redirect('task_list')

class TaskUpdateView(View):
    def get(self, request, pk):
        task = get_task_by_id(pk)
        if not task:
            return redirect('task_list')
        
        # Format date for template if it exists
        if task['due_date']:
            task['due_date_formatted'] = task['due_date'].strftime('%Y-%m-%d')
        
        return render(request, 'tasks/task_form.html', {'task': task})

    def post(self, request, pk):
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        due_date = request.POST.get('due_date') or None
        status = request.POST.get('status', 'pending')

        if title:
            update_task(pk, title, description, due_date, status)
        return redirect('task_list')

class TaskDeleteView(View):
    def post(self, request, pk):
        delete_task(pk)
        return redirect('task_list')