// Project filtering functionality
document.addEventListener('DOMContentLoaded', function() {
    const categoryFilter = document.getElementById('categoryFilter');
    const technologyFilter = document.getElementById('technologyFilter');
    const resetButton = document.getElementById('resetFilters');
    const projectsGrid = document.getElementById('projectsGrid');
    const noResults = document.getElementById('noResults');
    
    function filterProjects() {
        const selectedCategory = categoryFilter.value;
        const selectedTechnology = technologyFilter.value;
        const projects = projectsGrid.querySelectorAll('.project-card');
        let visibleCount = 0;
        
        projects.forEach(project => {
            const projectCategory = project.dataset.category;
            const projectTechnologies = project.dataset.technologies;
            
            const categoryMatch = !selectedCategory || projectCategory === selectedCategory;
            const technologyMatch = !selectedTechnology || projectTechnologies.includes(selectedTechnology);
            
            if (categoryMatch && technologyMatch) {
                project.style.display = 'block';
                visibleCount++;
            } else {
                project.style.display = 'none';
            }
        });
        
        noResults.style.display = visibleCount === 0 ? 'block' : 'none';
    }
    
    categoryFilter.addEventListener('change', filterProjects);
    technologyFilter.addEventListener('change', filterProjects);
    
    resetButton.addEventListener('click', function() {
        categoryFilter.value = '';
        technologyFilter.value = '';
        filterProjects();
    });
});
