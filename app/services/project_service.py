"""
Project service layer.
Handles all project-related business logic and data operations.
"""
from app.models import db, Project, RaspberryPiProject
from app.services import BaseService, cache_result, invalidate_cache_pattern
from typing import List, Optional, Dict, Any


class ProjectService(BaseService):
    """Service for project operations."""
    
    @cache_result(timeout=600, key_prefix='project:all')
    def get_all_projects(self) -> List[Project]:
        """
        Get all projects.
        
        Returns:
            List of all projects
        """
        return Project.query.all()
    
    @cache_result(timeout=600, key_prefix='project:featured')
    def get_featured_projects(self, limit: int = 3) -> List[Project]:
        """
        Get featured projects.
        
        Args:
            limit: Number of featured projects to return
            
        Returns:
            List of featured projects
        """
        return Project.query.filter_by(featured=True).limit(limit).all()
    
    @cache_result(timeout=600, key_prefix='project:category')
    def get_by_category(self, category: str) -> List[Project]:
        """
        Get projects by category.
        
        Args:
            category: Category name
            
        Returns:
            List of projects in category
        """
        return Project.query.filter_by(category=category).all()
    
    @cache_result(timeout=600, key_prefix='project:technology')
    def get_by_technology(self, technology: str) -> List[Project]:
        """
        Get projects by technology.
        
        Args:
            technology: Technology name
            
        Returns:
            List of projects using technology
        """
        return Project.query.filter(
            Project.technologies.contains(technology)
        ).all()
    
    @cache_result(timeout=600, key_prefix='project:detail')
    def get_by_id(self, project_id: int) -> Optional[Project]:
        """
        Get project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            Project or None
        """
        return Project.query.get(project_id)
    
    def create_project(self, data: Dict[str, Any]) -> Project:
        """
        Create new project.
        
        Args:
            data: Project data dictionary
            
        Returns:
            Created Project
        """
        project = Project(**data)
        db.session.add(project)
        db.session.commit()
        
        # Invalidate project cache
        self._invalidate_project_cache()
        
        return project
    
    def update_project(self, project_id: int, data: Dict[str, Any]) -> Optional[Project]:
        """
        Update project.
        
        Args:
            project_id: Project ID
            data: Updated project data
            
        Returns:
            Updated Project or None
        """
        project = Project.query.get(project_id)
        if not project:
            return None
        
        # Update fields
        for key, value in data.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        db.session.commit()
        
        # Invalidate project cache
        self._invalidate_project_cache()
        
        return project
    
    def delete_project(self, project_id: int) -> bool:
        """
        Delete project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if deleted, False otherwise
        """
        project = Project.query.get(project_id)
        if not project:
            return False
        
        db.session.delete(project)
        db.session.commit()
        
        # Invalidate project cache
        self._invalidate_project_cache()
        
        return True
    
    def to_dict(self, project: Project) -> Dict[str, Any]:
        """
        Convert project to dictionary for JSON serialization.
        
        Args:
            project: Project instance
            
        Returns:
            Project data as dictionary
        """
        return {
            'id': project.id,
            'title': project.title,
            'description': project.description,
            'technologies': [t.strip() for t in project.technologies.split(',')] if project.technologies else [],
            'category': project.category,
            'image': project.image_url,
            'github': project.github_url,
            'demo': project.demo_url,
            'featured': project.featured
        }
    
    def _invalidate_project_cache(self) -> None:
        """Invalidate all project-related cache entries."""
        patterns = ['project:all', 'project:featured', 'project:category', 
                   'project:technology', 'project:detail']
        for pattern in patterns:
            invalidate_cache_pattern(pattern)


class RaspberryPiService(BaseService):
    """Service for Raspberry Pi project operations."""
    
    @cache_result(timeout=600, key_prefix='rpi:all')
    def get_all_projects(self) -> List[RaspberryPiProject]:
        """
        Get all Raspberry Pi projects.
        
        Returns:
            List of all Raspberry Pi projects
        """
        return RaspberryPiProject.query.all()
    
    @cache_result(timeout=600, key_prefix='rpi:detail')
    def get_by_id(self, project_id: int) -> Optional[RaspberryPiProject]:
        """
        Get Raspberry Pi project by ID.
        
        Args:
            project_id: Project ID
            
        Returns:
            RaspberryPiProject or None
        """
        return RaspberryPiProject.query.get(project_id)
    
    def create_project(self, data: Dict[str, Any]) -> RaspberryPiProject:
        """
        Create new Raspberry Pi project.
        
        Args:
            data: Project data dictionary
            
        Returns:
            Created RaspberryPiProject
        """
        project = RaspberryPiProject(**data)
        db.session.add(project)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache_pattern('rpi:all')
        
        return project
    
    def update_project(self, project_id: int, data: Dict[str, Any]) -> Optional[RaspberryPiProject]:
        """
        Update Raspberry Pi project.
        
        Args:
            project_id: Project ID
            data: Updated project data
            
        Returns:
            Updated RaspberryPiProject or None
        """
        project = RaspberryPiProject.query.get(project_id)
        if not project:
            return None
        
        for key, value in data.items():
            if hasattr(project, key):
                setattr(project, key, value)
        
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache_pattern('rpi:all')
        invalidate_cache_pattern('rpi:detail')
        
        return project
    
    def delete_project(self, project_id: int) -> bool:
        """
        Delete Raspberry Pi project.
        
        Args:
            project_id: Project ID
            
        Returns:
            True if deleted, False otherwise
        """
        project = RaspberryPiProject.query.get(project_id)
        if not project:
            return False
        
        db.session.delete(project)
        db.session.commit()
        
        # Invalidate cache
        invalidate_cache_pattern('rpi:all')
        invalidate_cache_pattern('rpi:detail')
        
        return True


# Global instances
project_service = ProjectService()
rpi_service = RaspberryPiService()
