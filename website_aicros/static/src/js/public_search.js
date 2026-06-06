odoo.define('website_aicros.public_search', function (require) {
    'use strict';

    function performSearch(event) {
        event.preventDefault();
        const form = document.getElementById('search_form');
        const formData = new FormData(form);
        const tableContainer = document.getElementById('request_table');
        const loadingSpinner = document.createElement('div');
        loadingSpinner.className = 'text-center p-3';
        loadingSpinner.innerHTML = '<i class="fa fa-spinner fa-spin fa-2x"></i>';
        
        tableContainer.style.display = 'none';
        tableContainer.parentNode.insertBefore(loadingSpinner, tableContainer);

        fetch('/public/professional/search', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            updateTable(data);
            document.getElementById('total_records').textContent = data.total_registers;
            loadingSpinner.remove();
            tableContainer.style.display = 'block';
            document.getElementById('closeTableButton').style.display = 'block';
        })
        .catch(error => {
            console.error('Error:', error);
            loadingSpinner.innerHTML = '<div class="alert alert-danger">Error al cargar los datos</div>';
        });
    }

    function showDetails(button) {
        const recordId = button.getAttribute('data-record-id');
        const modal = $('#detailsModal');
        const content = document.getElementById('detailsContent');
        
        content.innerHTML = '<div class="text-center"><i class="fa fa-spinner fa-spin fa-2x"></i></div>';
        modal.modal('show');
        
        fetch(`/public/professional/details/${recordId}`)
        .then(response => response.json())
        .then(data => {
            content.innerHTML = '';
            
            // Group fields by their group type
            const groups = {};
            for (const [field, info] of Object.entries(data)) {
                const group = info.group || 'other';
                if (!groups[group]) {
                    groups[group] = [];
                }
                groups[group].push({ field, info });
            }
            
            // Create sections for each group
            for (const [group, fields] of Object.entries(groups)) {
                const section = document.createElement('div');
                section.className = 'mb-4';
                section.innerHTML = `<h5 class="border-bottom pb-2">${capitalizeFirstLetter(group)}</h5>`;
                
                fields.forEach(({ field, info }) => {
                    section.innerHTML += `
                        <div class="row mb-2">
                            <div class="col-sm-4"><strong>${info.label}:</strong></div>
                            <div class="col-sm-8">${info.value || ''}</div>
                        </div>
                    `;
                });
                
                content.appendChild(section);
            }
        })
        .catch(error => {
            content.innerHTML = '<div class="alert alert-danger">Error al cargar los detalles</div>';
        });
    }

    function updateTable(data) {
        const tbody = document.querySelector('#request_table tbody');
        tbody.innerHTML = '';

        data.register_list.forEach((record, index) => {
            const row = document.createElement('tr');
            
            // Add index column
            row.innerHTML = `<td>${index + 1}</td>`;
            
            // Add fields based on main_fields configuration
            data.main_fields.forEach(field => {
                const fieldData = record[field.name];
                row.innerHTML += `<td>${fieldData?.value || ''}</td>`;
            });
            
            // Add details button
            row.innerHTML += `
                <td>
                    <button class="btn btn-info btn-sm" 
                            onclick="showDetails(this)" 
                            data-record-id="${record.record_id}">
                        Ver más
                    </button>
                </td>
            `;
            
            tbody.appendChild(row);
        });
    }

    function capitalizeFirstLetter(string) {
        return string.charAt(0).toUpperCase() + string.slice(1);
    }

    // Initialize search form and specialty dropdown
    document.addEventListener('DOMContentLoaded', function () {
        const searchForm = document.getElementById('search_form');
        if (searchForm) {
            searchForm.addEventListener('submit', performSearch);
        }

        // Handle profession change for specialties
        const professionSelect = document.getElementById('professions');
        const specialtySelect = document.getElementById('specialties');
        
        if (professionSelect && specialtySelect) {
            professionSelect.addEventListener('change', function() {
                const professionId = this.value;
                
                specialtySelect.innerHTML = '<option value="">Cargando...</option>';
                
                fetch(`/web/get_specialties?profession_id=${professionId}`)
                    .then(response => response.json())
                    .then(data => {
                        specialtySelect.innerHTML = '<option value="">Especialidad</option>';
                        data.forEach(specialty => {
                            specialtySelect.innerHTML += `
                                <option value="${specialty.id}">${specialty.name}</option>
                            `;
                        });
                    })
                    .catch(() => {
                        specialtySelect.innerHTML = '<option value="">Error al cargar especialidades</option>';
                    });
            });
        }
    });
});