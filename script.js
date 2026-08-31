document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const loginView = document.getElementById('login-view');
    const dashboardView = document.getElementById('dashboard-view');
    const loginForm = document.getElementById('login-form');
    const loginBtn = document.getElementById('login-btn');
    const errorMsg = document.getElementById('login-error');
    const logoutBtn = document.getElementById('logout-btn');
    const userGreeting = document.getElementById('user-greeting');
    const subjectsContainer = document.getElementById('subjects-container');
    const todaysContainer = document.getElementById('todays-container');
    const targetBtns = document.querySelectorAll('.btn-target');
    const scraperWarning = document.getElementById('scraper-warning');
    const tabBtns = document.querySelectorAll('.btn-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const routineTbody = document.getElementById('routine-tbody');
    const academicsBtn = document.getElementById('academics-btn');
    const academicsDropdown = document.getElementById('academics-dropdown');
    const navInfo = document.getElementById('nav-info');
    const infoModal = document.getElementById('info-modal');
    const closeModalBtn = infoModal.querySelector('.close-modal');
    const infoModalBody = document.getElementById('info-modal-body');
    const navCrDashboard = document.getElementById('nav-cr-dashboard');
    const crDashboardView = document.getElementById('cr-dashboard-view');
    const backToDashboardBtn = document.getElementById('back-to-dashboard-btn');
    const crDatePicker = document.getElementById('cr-date-picker');
    const crExportBtn = document.getElementById('cr-export-btn');
    const crAttendanceList = document.getElementById('cr-attendance-list');
    const addStudentForm = document.getElementById('add-student-form');
    const addRollInput = document.getElementById('add-roll');
    const addNameInput = document.getElementById('add-name');
    const crSectionLabel = document.getElementById('cr-section-label');
    const userSection = document.getElementById('user-section');
    const themeToggleBtns = document.querySelectorAll('.theme-toggle-btn');

    // Theme Toggle Logic
    const toggleTheme = () => {
        const currentTheme = document.body.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        // Update icons
        themeToggleBtns.forEach(btn => {
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) icon.setAttribute('data-lucide', newTheme === 'dark' ? 'sun' : 'moon');
                lucide.createIcons({ root: btn });
            }
        });
    };

    themeToggleBtns.forEach(btn => {
        if (btn) btn.addEventListener('click', toggleTheme);
    });

    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark') {
        document.body.setAttribute('data-theme', 'dark');
        themeToggleBtns.forEach(btn => {
            if (btn) {
                const icon = btn.querySelector('i');
                if (icon) icon.setAttribute('data-lucide', 'sun');
            }
        });
    }

    // State
    let currentData = null;
    let targetPercentage = 0.85;

    // Check if already logged in (using sessionStorage for demo)
    const storedData = sessionStorage.getItem('attendanceData');
    if (storedData) {
        currentData = JSON.parse(storedData);
        showDashboard();
    }

    // Login Handler
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        loginBtn.disabled = true;
        loginBtn.innerHTML = '<i data-lucide="loader" class="spin"></i><span>Authenticating...</span>';
        lucide.createIcons();
        errorMsg.textContent = '';

        try {
            const response = await fetch('/api/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });

            const result = await response.json();

            if (result.success) {
                currentData = result.data;
                sessionStorage.setItem('attendanceData', JSON.stringify(currentData));
                
                if (result.message) {
                    scraperWarning.style.display = 'flex';
                } else {
                    scraperWarning.style.display = 'none';
                }

                showDashboard();
            } else {
                errorMsg.textContent = result.error || 'Login failed';
            }
        } catch (err) {
            errorMsg.textContent = 'Server error. Is the backend running?';
        } finally {
            loginBtn.disabled = false;
            loginBtn.innerHTML = '<span>Authenticate</span><i data-lucide="arrow-right"></i>';
            lucide.createIcons();
        }
    });

    // Logout
    logoutBtn.addEventListener('click', () => {
        sessionStorage.removeItem('attendanceData');
        currentData = null;
        dashboardView.classList.remove('active');
        setTimeout(() => {
            loginView.classList.add('active');
            loginForm.reset();
        }, 400);
    });

    // Target Selection
    targetBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            targetBtns.forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            targetPercentage = parseInt(e.target.dataset.target) / 100;
            renderSubjects();
        });
    });

    // Tab Selection
    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            // Update buttons
            tabBtns.forEach(b => {
                b.classList.remove('active');
                b.style.background = 'transparent';
                b.style.color = 'rgba(255,255,255,0.7)';
            });
            const clickedBtn = e.target;
            clickedBtn.classList.add('active');
            clickedBtn.style.background = 'rgba(255,255,255,0.1)';
            clickedBtn.style.color = 'white';

            // Update content
            tabContents.forEach(content => {
                content.style.display = 'none';
                content.classList.remove('active');
            });
            const targetTab = document.getElementById(clickedBtn.dataset.tab);
            targetTab.style.display = 'block';
            setTimeout(() => targetTab.classList.add('active'), 10);
        });
    });

    // Dropdown Toggle
    academicsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        academicsBtn.parentElement.classList.toggle('show');
    });

    // Close dropdown on outside click
    document.addEventListener('click', () => {
        academicsBtn.parentElement.classList.remove('show');
    });

    academicsDropdown.addEventListener('click', (e) => {
        e.stopPropagation();
    });

    // Modal Logic
    navInfo.addEventListener('click', (e) => {
        e.preventDefault();
        academicsBtn.parentElement.classList.remove('show');
        renderPersonalInfo();
        infoModal.classList.add('active');
    });

    if (navCrDashboard) {
        navCrDashboard.addEventListener('click', (e) => {
            e.preventDefault();
            academicsBtn.parentElement.classList.remove('show');
            dashboardView.classList.remove('active');
            setTimeout(() => {
                crDashboardView.classList.add('active');
                if (crStudentsData.length === 0) {
                    initCRDashboard();
                }
            }, 400);
        });
    }

    if (backToDashboardBtn) {
        backToDashboardBtn.addEventListener('click', () => {
            crDashboardView.classList.remove('active');
            setTimeout(() => {
                dashboardView.classList.add('active');
            }, 400);
        });
    }

    closeModalBtn.addEventListener('click', () => {
        infoModal.classList.remove('active');
    });

    infoModal.addEventListener('click', (e) => {
        if (e.target === infoModal) {
            infoModal.classList.remove('active');
        }
    });

    function renderPersonalInfo() {
        infoModalBody.innerHTML = '';
        if (!currentData || !currentData.personalInfo || Object.keys(currentData.personalInfo).length === 0) {
            infoModalBody.innerHTML = '<p style="text-align:center; color: var(--text-muted);">No personal information available.</p>';
            return;
        }

        // Recursive function to render nested objects
        function renderNode(node, container, level = 0) {
            if (Array.isArray(node)) {
                // Render array of objects (like Educational Details)
                const table = document.createElement('table');
                table.style.width = '100%';
                table.style.borderCollapse = 'collapse';
                table.style.marginTop = '10px';
                table.style.marginBottom = '15px';
                
                if (node.length > 0) {
                    const thead = document.createElement('thead');
                    const trHead = document.createElement('tr');
                    Object.keys(node[0]).forEach(key => {
                        const th = document.createElement('th');
                        th.textContent = key;
                        th.style.padding = '8px';
                        th.style.background = 'rgba(255,255,255,0.1)';
                        th.style.textAlign = 'left';
                        th.style.fontSize = '0.85rem';
                        trHead.appendChild(th);
                    });
                    thead.appendChild(trHead);
                    table.appendChild(thead);
                    
                    const tbody = document.createElement('tbody');
                    node.forEach(rowObj => {
                        const tr = document.createElement('tr');
                        Object.values(rowObj).forEach(val => {
                            const td = document.createElement('td');
                            td.textContent = val;
                            td.style.padding = '8px';
                            td.style.borderBottom = '1px solid rgba(255,255,255,0.05)';
                            td.style.fontSize = '0.9rem';
                            tr.appendChild(td);
                        });
                        tbody.appendChild(tr);
                    });
                    table.appendChild(tbody);
                }
                container.appendChild(table);
            } else if (typeof node === 'object' && node !== null) {
                // Render object (key-value pairs or nested categories)
                Object.entries(node).forEach(([key, value]) => {
                    // Check if value is a string (or empty object meaning no subdata)
                    if (typeof value === 'string') {
                        const item = document.createElement('div');
                        item.className = 'info-item';
                        item.style.paddingLeft = `${level * 15}px`;
                        
                        // Check if value looks like an image URL
                        if (value.startsWith('http') && (value.includes('.jpeg') || value.includes('.jpg') || value.includes('.png') || value.includes('.gif'))) {
                            item.innerHTML = `
                                <span class="info-label">${key}</span>
                                <span class="info-value"><img src="${value}" alt="${key}" style="max-width: 150px; border-radius: 8px; margin-top: 5px;"></span>
                            `;
                        } else {
                            item.innerHTML = `
                                <span class="info-label">${key}</span>
                                <span class="info-value">${value}</span>
                            `;
                        }
                        container.appendChild(item);
                    } else if (Object.keys(value).length > 0) {
                        // It's a nested category
                        const header = document.createElement('h4');
                        header.textContent = key;
                        header.style.color = 'var(--primary)';
                        header.style.marginTop = '1.5rem';
                        header.style.marginBottom = '1rem';
                        header.style.paddingBottom = '0.5rem';
                        header.style.borderBottom = '1px solid rgba(255,255,255,0.1)';
                        header.style.fontSize = level === 0 ? '1.1rem' : '0.95rem';
                        header.style.marginLeft = `${level * 15}px`;
                        container.appendChild(header);
                        
                        renderNode(value, container, level + 1);
                    }
                });
            }
        }

        renderNode(currentData.personalInfo, infoModalBody, 0);
    }

    function showDashboard() {
        loginView.classList.remove('active');
        userGreeting.textContent = `Hello, ${currentData.studentName}`;
        
        const userAvatar = document.getElementById('user-avatar');
        if (currentData.profilePhoto) {
            userAvatar.src = currentData.profilePhoto;
            userAvatar.onerror = function() {
                this.style.display = 'none';
            };
            userAvatar.style.display = 'block';
        } else {
            userAvatar.style.display = 'none';
        }

        setTimeout(() => {
            dashboardView.classList.add('active');
            renderSubjects();
            renderRoutine();
            renderTodaysAttendance();
            
            // Check CR status and show link if true
            if (currentData.is_cr) {
                navCrDashboard.style.display = 'block';
            } else {
                navCrDashboard.style.display = 'none';
            }

            if (currentData.section && userSection) {
                userSection.innerText = `| ${currentData.section}`;
            } else if (userSection) {
                userSection.innerText = '';
            }

            if (currentData.subjects && currentData.subjects.length > 0) {
                // Initial CR Dashboard rendering logic placeholder
            }
        }, 400);
    }

    function calculateAction(attended, total, target) {
        const currentPerc = total === 0 ? 0 : attended / total;
        
        if (currentPerc >= target) {
            // Can skip classes
            // Formula: attended / (total + y) = target => y = (attended - target*total) / target
            const y = Math.floor((attended - target * total) / target);
            return {
                type: 'skip',
                count: y,
                message: y > 0 ? `You can safely bunk ${y} class${y > 1 ? 'es' : ''}.` : `On track. Don't skip next class.`,
                statusClass: 'status-good',
                bgClass: 'bg-good',
                icon: 'check-circle'
            };
        } else {
            // Need to attend classes
            // Formula: (attended + x) / (total + x) = target => x = (target*total - attended) / (1 - target)
            const x = Math.ceil((target * total - attended) / (1 - target));
            
            // If it's mathematically impossible (e.g., target is 100%), handle it
            if (x === Infinity) {
                return {
                    type: 'attend',
                    count: x,
                    message: `Impossible to reach ${target*100}%.`,
                    statusClass: 'status-bad',
                    bgClass: 'bg-bad',
                    icon: 'alert-octagon'
                };
            }

            return {
                type: 'attend',
                count: x,
                message: `Attend next ${x} class${x > 1 ? 'es' : ''} to reach ${target*100}%.`,
                statusClass: 'status-warn',
                bgClass: 'bg-warn',
                icon: 'alert-triangle'
            };
        }
    }

    // Toast Notification System
    function showToast(title, message, isWarning = false) {
        const container = document.getElementById('toast-container');
        if (!container) return;

        const toast = document.createElement('div');
        toast.className = 'toast';
        if (!isWarning) {
            toast.style.borderLeftColor = 'var(--good)';
        }

        const iconColorClass = isWarning ? 'var(--danger)' : 'var(--good)';
        const iconName = isWarning ? 'alert-triangle' : 'check-circle';

        toast.innerHTML = `
            <div class="toast-icon" style="color: ${iconColorClass}">
                <i data-lucide="${iconName}"></i>
            </div>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                <div class="toast-message">${message}</div>
            </div>
        `;

        container.appendChild(toast);
        lucide.createIcons({ root: toast });

        // Animate in
        setTimeout(() => {
            toast.classList.add('show');
        }, 10);

        // Auto remove after 5 seconds
        setTimeout(() => {
            toast.classList.add('hiding');
            toast.addEventListener('transitionend', () => {
                toast.remove();
            });
        }, 5000);
    }

    function renderSubjects() {
        subjectsContainer.innerHTML = '';
        const template = document.getElementById('subject-card-template');
        let lowSubjectsCount = 0;

        currentData.subjects.forEach((subject, index) => {
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.subject-card');
            
            // Set basic info
            card.querySelector('.subject-name').textContent = subject.name;
            card.querySelector('.subject-name').title = subject.name; // Tooltip for long names
            card.querySelector('.attended-val').textContent = subject.attended;
            card.querySelector('.total-val').textContent = subject.total;

            const percentage = subject.total === 0 ? 0 : Math.round((subject.attended / subject.total) * 100);
            card.querySelector('.percentage-text').textContent = `${percentage}%`;

            // Calculate action
            const action = calculateAction(subject.attended, subject.total, targetPercentage);
            
            const actionBox = card.querySelector('.action-box');
            actionBox.classList.add(action.bgClass);
            actionBox.querySelector('.action-text').textContent = action.message;
            actionBox.querySelector('.status-icon').innerHTML = `<i data-lucide="${action.icon}" class="${action.statusClass}"></i>`;

            // Set progress circle
            const circle = card.querySelector('.circle');
            circle.classList.add(action.statusClass);
            
            // Need a slight delay for the CSS transition to work on first render
            setTimeout(() => {
                circle.setAttribute('stroke-dasharray', `${percentage}, 100`);
            }, 50 * index);

            if (percentage < (targetPercentage * 100)) {
                lowSubjectsCount++;
            }

            // Add animation
            card.classList.add('animate-fade-up');
            card.style.animationDelay = `${index * 0.1}s`;

            subjectsContainer.appendChild(clone);
        });

        lucide.createIcons();

        // Trigger real-time low attendance notification
        if (lowSubjectsCount > 0) {
            showToast(
                'Low Attendance Alert', 
                `You have ${lowSubjectsCount} subject${lowSubjectsCount > 1 ? 's' : ''} below your ${Math.round(targetPercentage * 100)}% target!`, 
                true
            );
        } else if (currentData.subjects.length > 0) {
            showToast(
                'Attendance Looks Good', 
                `All your subjects meet the ${Math.round(targetPercentage * 100)}% target!`, 
                false
            );
        }
    }

    function renderRoutine() {
        routineTbody.innerHTML = '';
        if (!currentData || !currentData.routine) {
            routineTbody.innerHTML = '<tr><td colspan="9" style="text-align: center; padding: 20px;">No routine data available.</td></tr>';
            return;
        }

        currentData.routine.forEach(day => {
            const tr = document.createElement('tr');
            
            // Day column
            const tdDay = document.createElement('td');
            tdDay.innerHTML = `<strong>${day.day}</strong>`;
            tdDay.style.padding = '10px';
            tdDay.style.background = 'rgba(255,255,255,0.05)';
            tdDay.style.borderRadius = '8px';
            tr.appendChild(tdDay);

            let expectedPeriod = 1;
            day.schedule.forEach(slot => {
                const td = document.createElement('td');
                td.colSpan = slot.colspan;
                td.style.padding = '10px';
                td.style.background = 'rgba(255,255,255,0.02)';
                td.style.borderRadius = '8px';
                td.style.textAlign = 'center';
                
                if (slot.subject) {
                    td.innerHTML = `
                        <div style="font-weight: 600; font-size: 0.9rem; color: #a5b4fc; text-transform: capitalize;">${slot.subject}</div>
                        <div style="font-size: 0.8rem; color: rgba(255,255,255,0.7); margin-top: 4px; text-transform: capitalize;">${slot.teacher}</div>
                        <div style="font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-top: 2px;">${slot.room}</div>
                    `;
                    td.style.border = '1px solid rgba(255,255,255,0.1)';
                } else {
                    td.innerHTML = '<span style="color: rgba(255,255,255,0.2);">-</span>';
                }
                tr.appendChild(td);
                expectedPeriod += slot.colspan;
            });

            // Fill any remaining empty slots if schedule array didn't go up to 8
            while (expectedPeriod <= 8) {
                const td = document.createElement('td');
                td.style.padding = '10px';
                td.style.background = 'rgba(255,255,255,0.02)';
                td.style.borderRadius = '8px';
                td.style.textAlign = 'center';
                td.innerHTML = '<span style="color: rgba(255,255,255,0.2);">-</span>';
                tr.appendChild(td);
                expectedPeriod++;
            }

            routineTbody.appendChild(tr);
        });
        lucide.createIcons();
    }

    function renderTodaysAttendance() {
        if (!todaysContainer) return;
        todaysContainer.innerHTML = '';
        
        if (!currentData || !currentData.routine || currentData.routine.length === 0) {
            todaysContainer.innerHTML = `<p style="text-align:center; color: var(--text-muted); width: 100%;">No class routine available to determine today's classes.</p>`;
            return;
        }

        // Determine today's day name (e.g., "Monday")
        const today = new Date().toLocaleDateString('en-US', { weekday: 'long' });
        
        // Find today's routine
        const todayRoutine = currentData.routine.find(r => r.day.startsWith(today) || r.day === today);
        
        if (!todayRoutine || !todayRoutine.schedule || todayRoutine.schedule.filter(s => s.subject).length === 0) {
            todaysContainer.innerHTML = `<p style="text-align:center; color: var(--text-muted); width: 100%;">No classes scheduled for today.</p>`;
            return;
        }
        
        const template = document.getElementById('subject-card-template');
        let index = 0;
        
        todayRoutine.schedule.forEach(slot => {
            if (!slot.subject) return;
            
            const clone = template.content.cloneNode(true);
            const card = clone.querySelector('.subject-card');
            
            // Adjust card to show today's specific info
            card.querySelector('.subject-name').textContent = slot.subject;
            card.querySelector('.subject-name').title = slot.subject;
            
            // Hide progress circle
            card.querySelector('.progress-circle-container').style.display = 'none';
            
            // Show time instead of attended/total
            const details = card.querySelector('.attendance-details');
            details.innerHTML = `
                <div class="detail" style="width: 100%;">
                    <span class="label">Teacher & Room</span>
                    <span class="value" style="font-size: 1rem; text-align: center;">${slot.teacher || 'N/A'}<br><small>${slot.room || ''}</small></span>
                </div>
            `;
            
            const actionBox = card.querySelector('.action-box');
            if (slot.attendance === 'Present') {
                actionBox.classList.add('bg-good');
                actionBox.querySelector('.action-text').textContent = 'Present';
                actionBox.querySelector('.status-icon').innerHTML = `<i data-lucide="check-circle" class="status-good"></i>`;
            } else if (slot.attendance === 'Absent') {
                actionBox.classList.add('bg-bad');
                actionBox.querySelector('.action-text').textContent = 'Absent';
                actionBox.querySelector('.status-icon').innerHTML = `<i data-lucide="x-circle" class="status-bad"></i>`;
            } else {
                actionBox.classList.add('bg-warn');
                actionBox.querySelector('.action-text').textContent = 'Not marked yet';
                actionBox.querySelector('.status-icon').innerHTML = `<i data-lucide="clock" class="status-warn"></i>`;
            }
            
            card.classList.add('animate-fade-up');
            card.style.animationDelay = `${index * 0.1}s`;
            index++;
            
            todaysContainer.appendChild(clone);
        });
        
        lucide.createIcons();
    }

    // CR Dashboard Logic
    let crStudentsData = [];
    
    async function saveCRStudents() {
        try {
            await fetch('/api/cr_students', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ students: crStudentsData })
            });
        } catch (e) {
            console.error("Failed to save CR students to server", e);
        }
    }

    async function loadCRStudents() {
        try {
            const resp = await fetch('/api/cr_students');
            const result = await resp.json();
            if (result.success && result.data && result.data.length > 0) {
                crStudentsData = result.data;
            } else {
                crStudentsData = [];
                // Auto-populate 351 to 384 for CRs on first load
                for (let i = 351; i <= 384; i++) {
                    crStudentsData.push({
                        rollNo: `UG/04/BTCSE/2025/${i}`,
                        name: '-',
                        status: 'Present'
                    });
                }
                saveCRStudents();
            }
        } catch (e) {
            console.error("Failed to load CR students from server", e);
        }
    }

    function renderCRStudents() {
        if (!crAttendanceList) return;
        crAttendanceList.innerHTML = '';
        
        crStudentsData.forEach((student, index) => {
            // Ensure status defaults to Present on fresh render if missing
            if (!student.status) student.status = 'Present';

            const row = document.createElement('div');
            row.className = 'cr-student-row';
            
            const isPresent = student.status === 'Present';
            const toggleClass = isPresent ? 'present' : 'absent';
            
            row.innerHTML = `
                <div>${index + 1}</div>
                <div>${student.rollNo}</div>
                <div style="text-transform: capitalize; font-size: 0.9rem;">${student.name}</div>
                <div>
                    <div class="status-toggle ${toggleClass}" data-index="${index}">
                        <div class="toggle-slider"></div>
                        <div class="toggle-option opt-p">P</div>
                        <div class="toggle-option opt-a">A</div>
                    </div>
                </div>
                <div style="display: flex; gap: 5px; justify-content: flex-end;">
                    <button class="edit-student-btn" data-index="${index}" title="Edit Name">
                        <i data-lucide="edit-2" style="width: 16px; height: 16px;"></i>
                    </button>
                    <button class="remove-student-btn" data-index="${index}" title="Remove Student">
                        <i data-lucide="trash-2" style="width: 16px; height: 16px;"></i>
                    </button>
                </div>
            `;
            
            crAttendanceList.appendChild(row);
        });

        lucide.createIcons();

        // Add event listeners to toggles
        const toggles = crAttendanceList.querySelectorAll('.status-toggle');
        toggles.forEach(toggle => {
            toggle.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                if (this.classList.contains('present')) {
                    this.classList.remove('present');
                    this.classList.add('absent');
                    crStudentsData[index].status = 'Absent';
                } else {
                    this.classList.remove('absent');
                    this.classList.add('present');
                    crStudentsData[index].status = 'Present';
                }
            });
        });

        // Add event listeners to remove buttons
        const removeBtns = crAttendanceList.querySelectorAll('.remove-student-btn');
        removeBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                crStudentsData.splice(index, 1);
                saveCRStudents();
                renderCRStudents();
            });
        });

        // Add event listeners to edit buttons
        const editBtns = crAttendanceList.querySelectorAll('.edit-student-btn');
        editBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const index = this.getAttribute('data-index');
                const student = crStudentsData[index];
                const currentName = student.name !== '-' ? student.name : '';
                const newName = prompt(`Enter new name for Roll ${student.rollNo}:`, currentName);
                
                if (newName !== null && newName.trim() !== '') {
                    student.name = newName.trim();
                    saveCRStudents();
                    renderCRStudents();
                }
            });
        });
    }

    async function initCRDashboard() {
        if (!crAttendanceList) return;
        
        if (crSectionLabel && currentData && currentData.section) {
            crSectionLabel.innerText = currentData.section;
        }

        // Initialize date picker to today (local timezone)
        if (crDatePicker) {
            const today = new Date();
            const yyyy = today.getFullYear();
            const mm = String(today.getMonth() + 1).padStart(2, '0');
            const dd = String(today.getDate()).padStart(2, '0');
            crDatePicker.value = `${yyyy}-${mm}-${dd}`;
        }

        await loadCRStudents();
        renderCRStudents();
    }

    if (addStudentForm) {
        addStudentForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const rollNo = addRollInput.value.trim();
            const name = addNameInput.value.trim();
            
            if (rollNo && name) {
                crStudentsData.push({
                    rollNo: rollNo,
                    name: name,
                    status: 'Present'
                });
                saveCRStudents();
                renderCRStudents();
                
                addRollInput.value = '';
                addNameInput.value = '';
                addRollInput.focus();
            }
        });
    }

    if (crExportBtn) {
        crExportBtn.addEventListener('click', () => {
            const dateVal = crDatePicker.value;
            if (!dateVal) {
                alert("Please select a date first.");
                return;
            }

            if (crStudentsData.length === 0) {
                alert("No students in the list. Add some students first.");
                return;
            }

            try {
                const { jsPDF } = window.jspdf;
                const doc = new jsPDF();
                
                // Add Header
                doc.setFontSize(18);
                doc.setTextColor(30, 41, 59);
                doc.text("Batch Attendance Register", 14, 22);
                
                doc.setFontSize(11);
                doc.setTextColor(100, 116, 139);
                doc.text(`Date: ${dateVal}`, 14, 30);
                
                const sectionText = (currentData && currentData.section) ? currentData.section : "Custom List";
                doc.text(`${sectionText} | Total Students: ${crStudentsData.length}`, 14, 36);

                // Calculate summary
                const presentCount = crStudentsData.filter(s => s.status === 'Present').length;
                const absentCount = crStudentsData.filter(s => s.status === 'Absent').length;
                doc.text(`Summary: ${presentCount} Present, ${absentCount} Absent`, 14, 42);

                // Prepare table data
                const tableColumn = ["Sl No", "Roll Number", "Name", "Status"];
                const tableRows = [];

                crStudentsData.forEach((student, index) => {
                    tableRows.push([
                        index + 1,
                        student.rollNo,
                        student.name,
                        student.status
                    ]);
                });

                // Generate table using autoTable plugin
                doc.autoTable({
                    head: [tableColumn],
                    body: tableRows,
                    startY: 50,
                    theme: 'grid',
                    headStyles: { fillColor: [139, 92, 246] },
                    styles: { fontSize: 10, cellPadding: 3 },
                    didParseCell: function (data) {
                        // Color the status column based on value
                        if (data.section === 'body' && data.column.index === 3) {
                            if (data.cell.raw === 'Present') {
                                data.cell.styles.textColor = [16, 185, 129];
                                data.cell.styles.fontStyle = 'bold';
                            } else if (data.cell.raw === 'Absent') {
                                data.cell.styles.textColor = [239, 68, 68];
                                data.cell.styles.fontStyle = 'bold';
                            }
                        }
                    }
                });

                // Save PDF
                doc.save(`Attendance_${dateVal}.pdf`);
            } catch (err) {
                console.error("PDF generation failed:", err);
                alert("Could not generate PDF. Check console for errors.");
            }
        });
    }

    // Custom Cursor Logic
    const cursorDot = document.querySelector('.cursor-dot');
    const cursorOutline = document.querySelector('.cursor-outline');
    
    if (cursorDot && cursorOutline) {
        window.addEventListener('mousemove', (e) => {
            const posX = e.clientX;
            const posY = e.clientY;
            
            cursorDot.style.left = `${posX}px`;
            cursorDot.style.top = `${posY}px`;
            
            // Use Element.animate if supported for smooth trailing
            if (cursorOutline.animate) {
                cursorOutline.animate({
                    left: `${posX}px`,
                    top: `${posY}px`
                }, { duration: 500, fill: "forwards" });
            } else {
                cursorOutline.style.left = `${posX}px`;
                cursorOutline.style.top = `${posY}px`;
            }
        });

        // Add hover effect to interactive elements
        const addHoverEvents = () => {
            document.querySelectorAll('a, button, input, .status-toggle, .btn-tab, .btn-target').forEach(el => {
                // Remove first to avoid duplicates if called multiple times
                el.removeEventListener('mouseenter', addCursorHover);
                el.removeEventListener('mouseleave', removeCursorHover);
                
                el.addEventListener('mouseenter', addCursorHover);
                el.addEventListener('mouseleave', removeCursorHover);
            });
        };
        
        const addCursorHover = () => document.body.classList.add('cursor-hover');
        const removeCursorHover = () => document.body.classList.remove('cursor-hover');
        
        // Initial setup
        addHoverEvents();
        
        // Setup MutationObserver to watch for new interactive elements (like rendered subject cards)
        const observer = new MutationObserver((mutations) => {
            addHoverEvents();
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }

});
