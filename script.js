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

    function showDashboard() {
        loginView.classList.remove('active');
        userGreeting.textContent = `Hello, ${currentData.studentName}`;
        setTimeout(() => {
            dashboardView.classList.add('active');
            renderSubjects();
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
});
