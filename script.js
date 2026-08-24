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
    const targetBtns = document.querySelectorAll('.btn-target');
    const scraperWarning = document.getElementById('scraper-warning');
    const tabBtns = document.querySelectorAll('.btn-tab');
    const tabContents = document.querySelectorAll('.tab-content');
    const routineTbody = document.getElementById('routine-tbody');

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

    function renderSubjects() {
        subjectsContainer.innerHTML = '';
        const template = document.getElementById('subject-card-template');

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

            subjectsContainer.appendChild(clone);
        });

        lucide.createIcons();
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
    }
});
