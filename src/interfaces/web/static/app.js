// State Management
let masterKey = localStorage.getItem('conny_master_key') || '';
let selectedChatId = null;
let chatPollingInterval = null;
let activeTab = 'chats';

// Synchronously restore avatar from localStorage to prevent default Notionist image flash
const savedAvatar = localStorage.getItem('conny_avatar_url');
if (savedAvatar) {
    document.addEventListener('DOMContentLoaded', () => {
        const lgImg = document.getElementById('account-large-image');
        const sbImg = document.getElementById('sidebar-avatar-img');
        const busterUrl = savedAvatar.includes('?') ? `${savedAvatar}&t=${Date.now()}` : `${savedAvatar}?t=${Date.now()}`;
        if(lgImg) lgImg.src = busterUrl;
        if(sbImg) sbImg.src = busterUrl;
    });
}


// DOM Elements
const loginScreen = document.getElementById('login-screen');
const onboardingScreen = document.getElementById('onboarding-screen');
const dashboardLayout = document.getElementById('dashboard-layout');

// Theme Management
const themeToggle = document.getElementById('theme-toggle');
const currentTheme = localStorage.getItem('conny_theme');
if (currentTheme === 'dark') {
    document.body.classList.add('dark-theme');
    if (themeToggle) themeToggle.checked = true;
} else {
    document.body.classList.remove('dark-theme');
}

if (themeToggle) {
    themeToggle.addEventListener('change', (e) => {
        if (e.target.checked) {
            document.body.classList.add('dark-theme');
            localStorage.setItem('conny_theme', 'dark');
        } else {
            document.body.classList.remove('dark-theme');
            localStorage.setItem('conny_theme', 'light');
        }
    });
}

const loginForm = document.getElementById('login-form');
const loginError = document.getElementById('login-error');
const masterKeyInput = document.getElementById('master-key');

// Elementos de Acceso Estándar Multi-paso
const emailCheckForm = document.getElementById('email-check-form');
const loginEmailInput = document.getElementById('login-email');
const loginEmailDisplay = document.getElementById('login-email-display');
const stepEmailView = document.getElementById('step-email-view');
const stepPasswordView = document.getElementById('step-password-view');
const stepSignupView = document.getElementById('step-signup-view');
const stepSuccessView = document.getElementById('step-success-view');

const signupForm = document.getElementById('signup-form');
const signupEmailInput = document.getElementById('signup-email');
const signupNameInput = document.getElementById('signup-name');
const signupPhoneInput = document.getElementById('signup-phone');
const signupSpecialtySelect = document.getElementById('signup-specialty');
const signupPasswordInput = document.getElementById('signup-password');
const signupTokenInput = document.getElementById('signup-token');

const btnBackToEmail = document.getElementById('btn-back-to-email');
const btnSignupBack = document.getElementById('btn-signup-back');
const successAccessTokenInput = document.getElementById('success-access-token');
const btnCopyToken = document.getElementById('btn-copy-token');
const btnGoDashboard = document.getElementById('btn-go-dashboard');

const stepTokenDirectView = document.getElementById('step-token-direct-view');
const tokenDirectForm = document.getElementById('token-direct-form');
const loginDirectToken = document.getElementById('login-direct-token');
const btnToggleTokenLogin = document.getElementById('btn-toggle-token-login');
const btnBackToEmailFromToken = document.getElementById('btn-back-to-email-from-token');

const stepRegistrationOptionsView = document.getElementById('step-registration-options-view');
const btnSwitchToRegister = document.getElementById('btn-switch-to-register');
const btnRegisterEmail = document.getElementById('btn-register-email');
const authProvidersContainer = document.getElementById('auth-providers-container');
const authSocialDivider = document.getElementById('auth-social-divider');
const authModeToggleContainer = document.getElementById('auth-mode-toggle-container');

// Dev Console
const navDevConsoleBtn = document.getElementById('nav-dev-console-btn');
const btnRefreshInstances = document.getElementById('btn-refresh-instances');
const devInstancesTbody = document.getElementById('dev-instances-tbody');
const devPromptInstanceSelect = document.getElementById('dev-prompt-instance-select');
const devPromptTextarea = document.getElementById('dev-prompt-textarea');
const btnSavePrompt = document.getElementById('btn-save-prompt');
const promptStatusMsg = document.getElementById('prompt-status-msg');

const devModelInstanceSelect = document.getElementById('dev-model-instance-select');
const devModelSelect = document.getElementById('dev-model-select');
const btnApplyModel = document.getElementById('btn-apply-model');
const modelStatusMsg = document.getElementById('model-status-msg');

const devNewInstanceForm = document.getElementById('dev-new-instance-form');
const devNewName = document.getElementById('dev-new-name');
const devNewSector = document.getElementById('dev-new-sector');
const newInstanceStatusMsg = document.getElementById('new-instance-status-msg');

const devLogsInstanceSelect = document.getElementById('dev-logs-instance-select');
const devTerminalLogs = document.getElementById('dev-terminal-logs');

// Elementos de Acceso para Desarrolladores
const btnSwitchToDev = document.getElementById('btn-switch-to-dev');
const btnBackToAdmin = document.getElementById('btn-back-to-admin');
const standardLoginView = document.getElementById('standard-login-view');
const developerLoginView = document.getElementById('developer-login-view');

const tabDevLogin = document.getElementById('tab-dev-login');
const tabDevRegister = document.getElementById('tab-dev-register');
const devLoginTabContent = document.getElementById('dev-login-tab-content');
const devRegisterTabContent = document.getElementById('dev-register-tab-content');

const devLoginFormNew = document.getElementById('dev-login-form-new');
const devLoginEmail = document.getElementById('dev-login-email');
const devLoginPassword = document.getElementById('dev-login-password');
const devLoginError = document.getElementById('dev-login-error');

const devRegisterForm = document.getElementById('dev-register-form');
const devRegEmail = document.getElementById('dev-reg-email');
const devRegPassword = document.getElementById('dev-reg-password');
const devRegToken = document.getElementById('dev-reg-token');

let checkedEmail = '';

const onboardingForm = document.getElementById('onboarding-form');
const obClinicNameInput = document.getElementById('ob-clinic-name');
const obClinicPhoneInput = document.getElementById('ob-clinic-phone');
const obSectorSelect = document.getElementById('ob-sector');
const obServicesInput = document.getElementById('ob-services');

const navItems = document.querySelectorAll('.nav-item');
const tabViews = document.querySelectorAll('.tab-view');

const chatsList = document.getElementById('chats-list');
const chatSearch = document.getElementById('chat-search');
const chatWelcome = document.getElementById('chat-welcome');
const chatActiveWindow = document.getElementById('chat-active-window');
const activeRecipientName = document.getElementById('active-recipient-name');
const activeRecipientPhone = document.getElementById('active-recipient-phone');
const messagesScroller = document.getElementById('messages-scroller');
const chatSendForm = document.getElementById('chat-send-form');
const chatInputMessage = document.getElementById('chat-input-message');

const appointmentsTbody = document.getElementById('appointments-tbody');
const appointmentsEmpty = document.getElementById('appointments-empty');

const profileClinicName = document.getElementById('profile-clinic-name');
const profileClinicPhone = document.getElementById('profile-clinic-phone');
const clinicInitials = document.getElementById('clinic-initials');
const profileServicesList = document.getElementById('profile-services-list');
const calendarStatusBadge = document.getElementById('calendar-status-badge');

const adminChatForm = document.getElementById('admin-chat-form');
const adminChatInput = document.getElementById('admin-chat-input');
const adminChatMessages = document.getElementById('admin-chat-messages');

const settingsModal = document.getElementById('settings-modal');
const openSettingsBtn = document.getElementById('open-settings-btn');
const closeSettingsModal = document.getElementById('close-settings-modal');
const settingsForm = document.getElementById('settings-form');
const settingsClinicName = document.getElementById('settings-clinic-name');
const settingsSector = document.getElementById('settings-sector');
const settingsDemoMode = document.getElementById('settings-demo-mode');

// Core API Call Helper
async function apiCall(path, method = 'GET', body = null) {
    const headers = {
        'Content-Type': 'application/json'
    };
    if (masterKey) {
        headers['X-Master-Key'] = masterKey;
    }

    const config = {
        method,
        headers
    };

    if (body) {
        config.body = JSON.stringify(body);
    }

    try {
        const response = await fetch(path, config);
        if (response.status === 401) {
            handleLogout();
            throw new Error('Sesión no autorizada');
        }
        if (!response.ok) {
            const errData = await response.json().catch(() => ({}));
            throw new Error(errData.detail || `Error en la petición: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`API Call failed to ${path}:`, error);
        throw error;
    }
}

// Check initial configuration state
async function checkAuthAndSetup() {
    const urlParams = new URLSearchParams(window.location.search);
    const googleLogin = urlParams.get('google_login') === 'true';
    
    if (googleLogin) {
        const googleEmail = urlParams.get('email') || '';
        const googleName = urlParams.get('name') || '';
        const googleAvatar = urlParams.get('avatar') || '';
        
        showScreen('login');
        
        const standardLogin = document.getElementById('standard-login-view');
        const googleOnboarding = document.getElementById('google-onboarding-view');
        if (standardLogin && googleOnboarding) {
            standardLogin.classList.remove('active');
            googleOnboarding.classList.add('active');
        }
        
        const ownerInput = document.getElementById('gob-owner-name');
        const emailInput = document.getElementById('gob-email');
        if (ownerInput) ownerInput.value = googleName;
        if (emailInput) emailInput.value = googleEmail;
        window.googleAvatarUrl = googleAvatar;
        
        // Clean URL to prevent routing issues on manual page refresh
        window.history.replaceState({}, document.title, window.location.pathname);
        return;
    }

    if (window.location.pathname === '/sign-in' || window.location.pathname.endsWith('/sign-in')) {
        showScreen('login');
        return;
    }

    if (!masterKey) {
        showScreen('login');
        return;
    }
    
    try {
        const config = await apiCall('/config');
        if (!config.name) {
            showScreen('onboarding');
        } else {
            showScreen('dashboard');
            initDashboard(config);
        }
    } catch (err) {
        showScreen('login');
    }
}

function showScreen(screen) {
    loginScreen.classList.remove('active');
    onboardingScreen.classList.remove('active');
    dashboardLayout.classList.remove('active');

    if (screen === 'login') {
        history.pushState({}, '', '/sign-in');
        loginScreen.classList.add('active');
    } else if (screen === 'onboarding') {
        history.pushState({}, '', '/onboarding');
        onboardingScreen.classList.add('active');
    } else if (screen === 'dashboard') {
        history.pushState({}, '', '/chats');
        dashboardLayout.classList.add('active');
        
        // Mostrar botón de consola dev si es dev
        if (localStorage.getItem('conny_dev_mode') === 'true' && navDevConsoleBtn) {
            navDevConsoleBtn.style.display = 'flex';
        }
    }
}

function handleLogout() {
    masterKey = '';
    localStorage.removeItem('conny_master_key');
    localStorage.removeItem('conny_dev_mode');
    
    // Quitar badge de desarrollador si existe
    const devBadge = document.getElementById('conny-dev-badge');
    if (devBadge) devBadge.remove();
    
    selectedChatId = null;
    if (chatPollingInterval) {
        clearInterval(chatPollingInterval);
        chatPollingInterval = null;
    }
    showScreen('login');
}

// ── Developer Login Handlers ──
if (btnSwitchToDev) {
    btnSwitchToDev.addEventListener('click', (e) => {
        e.preventDefault();
        devLoginError.innerText = '';
        devLoginError.style.color = '';
        if (standardLoginView) standardLoginView.classList.remove('active');
        if (developerLoginView) {
            developerLoginView.style.display = 'block';
            setTimeout(() => {
                developerLoginView.classList.add('active');
            }, 10);
        }
    });
}

if (btnBackToAdmin) {
    btnBackToAdmin.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (developerLoginView) {
            developerLoginView.classList.remove('active');
            setTimeout(() => {
                developerLoginView.style.display = 'none';
            }, 300);
        }
        if (standardLoginView) standardLoginView.classList.add('active');
    });
}

// Developer Tabs Switching
if (tabDevLogin && tabDevRegister) {
    tabDevLogin.addEventListener('click', () => {
        tabDevLogin.classList.add('active');
        tabDevRegister.classList.remove('active');
        if (devLoginTabContent) devLoginTabContent.style.display = 'block';
        if (devRegisterTabContent) devRegisterTabContent.style.display = 'none';
        devLoginError.innerText = '';
        devLoginError.style.color = '';
    });

    tabDevRegister.addEventListener('click', () => {
        tabDevRegister.classList.add('active');
        tabDevLogin.classList.remove('active');
        if (devLoginTabContent) devLoginTabContent.style.display = 'none';
        if (devRegisterTabContent) devRegisterTabContent.style.display = 'block';
        devLoginError.innerText = '';
        devLoginError.style.color = '';
    });
}

// Developer Sign-in Submit
if (devLoginFormNew) {
    devLoginFormNew.addEventListener('submit', async (e) => {
        e.preventDefault();
        devLoginError.innerText = '';
        devLoginError.style.color = '';
        const email = devLoginEmail.value.trim();
        const password = devLoginPassword.value.trim();

        if (!email || !password) return;

        try {
            const res = await fetch('/api/auth/dev-login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Credenciales incorrectas');
            }

            const data = await res.json();
            if (data.master_key) {
                masterKey = data.master_key;
                localStorage.setItem('conny_master_key', masterKey);
                localStorage.setItem('conny_dev_mode', 'true');
                
                const config = await apiCall('/config');
                showDevBadge();
                showScreen('dashboard');
                initDashboard(config);
            } else {
                throw new Error('No se recibió la llave maestra.');
            }
        } catch (err) {
            masterKey = '';
            localStorage.removeItem('conny_master_key');
            localStorage.removeItem('conny_dev_mode');
            devLoginError.innerText = err.message || 'Error de conexión con el servidor.';
        }
    });
}

// Developer Register Submit
if (devRegisterForm) {
    devRegisterForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        devLoginError.innerText = '';
        devLoginError.style.color = '';
        const email = devRegEmail.value.trim();
        const password = devRegPassword.value.trim();
        const devToken = devRegToken.value.trim();

        if (!email || !password || !devToken) return;

        try {
            const res = await fetch('/api/auth/dev-register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email, password, dev_token: devToken })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Error al registrar la cuenta de desarrollador');
            }

            const data = await res.json();
            
            // Show premium success style
            devLoginError.style.color = '#34a853';
            devLoginError.innerText = '¡Cuenta registrada con éxito! Inicia sesión para continuar.';
            
            // Pre-fill and clean fields
            devLoginEmail.value = email;
            devLoginPassword.value = '';
            devRegPassword.value = '';
            devRegToken.value = '';

            // Switch to Login tab after 1.5s delay
            setTimeout(() => {
                if (tabDevLogin) tabDevLogin.click();
                devLoginPassword.focus();
            }, 1500);

        } catch (err) {
            devLoginError.style.color = '';
            devLoginError.innerText = err.message || 'Error de conexión con el servidor.';
        }
    });
}

function showDevBadge() {
    const isDev = localStorage.getItem('conny_dev_mode') === 'true';
    const existing = document.getElementById('conny-dev-badge');
    if (existing) existing.remove();

    if (isDev) {
        const brandHeader = document.querySelector('.brand-header-crop');
        if (brandHeader) {
            const badge = document.createElement('div');
            badge.id = 'conny-dev-badge';
            badge.innerText = 'DEV';
            badge.style.cssText = `
                font-size: 10px;
                font-weight: 700;
                background: linear-gradient(135deg, #8b5cf6, #3b82f6);
                color: white;
                padding: 3px 8px;
                border-radius: 20px;
                margin-left: 8px;
                letter-spacing: 0.5px;
                box-shadow: 0 0 10px rgba(139, 92, 246, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.2);
                flex-shrink: 0;
            `;
            // Insert after the logo image
            const logo = brandHeader.querySelector('.brand-logo-cropped');
            if (logo) {
                logo.after(badge);
            } else {
                brandHeader.prepend(badge);
            }
        }
        if (navDevConsoleBtn) navDevConsoleBtn.style.display = 'flex';
    }
}

// ── Standard Multi-Step Onboarding Handlers ──

// Toggles for Direct Token and Registration
if (btnToggleTokenLogin) {
    btnToggleTokenLogin.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (stepEmailView) stepEmailView.style.display = 'none';
        if (authProvidersContainer) authProvidersContainer.style.display = 'none';
        if (authSocialDivider) authSocialDivider.style.display = 'none';
        if (authModeToggleContainer) authModeToggleContainer.style.display = 'none';
        if (stepTokenDirectView) stepTokenDirectView.style.display = 'block';
        if (loginDirectToken) loginDirectToken.focus();
    });
}

if (btnBackToEmailFromToken) {
    btnBackToEmailFromToken.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (stepTokenDirectView) stepTokenDirectView.style.display = 'none';
        if (stepEmailView) stepEmailView.style.display = 'block';
        if (authProvidersContainer) authProvidersContainer.style.display = 'flex';
        if (authSocialDivider) authSocialDivider.style.display = 'block';
        if (authModeToggleContainer) authModeToggleContainer.style.display = 'flex';
        if (loginEmailInput) loginEmailInput.focus();
    });
}

if (tokenDirectForm) {
    tokenDirectForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.innerText = '';
        const password = loginDirectToken.value.trim();
        if (!password) return;
        
        masterKey = password;
        try {
            const config = await apiCall('/config');
            localStorage.setItem('conny_master_key', password);
            if (!config.name) {
                showScreen('onboarding');
            } else {
                showScreen('dashboard');
                initDashboard(config);
            }
        } catch (fallbackErr) {
            masterKey = '';
            localStorage.removeItem('conny_master_key');
            loginError.innerText = 'Llave Maestra o Token de Acceso inválido.';
        }
    });
}

if (btnSwitchToRegister) {
    btnSwitchToRegister.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (stepEmailView) stepEmailView.style.display = 'none';
        if (authModeToggleContainer) authModeToggleContainer.style.display = 'none';
        if (stepRegistrationOptionsView) stepRegistrationOptionsView.style.display = 'block';
    });
}

if (btnRegisterEmail) {
    btnRegisterEmail.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (stepRegistrationOptionsView) stepRegistrationOptionsView.style.display = 'none';
        if (authProvidersContainer) authProvidersContainer.style.display = 'none';
        if (authSocialDivider) authSocialDivider.style.display = 'none';
        if (stepSignupView) stepSignupView.style.display = 'block';
        if (signupEmailInput && loginEmailInput) {
            signupEmailInput.value = loginEmailInput.value;
        }
        if (signupNameInput) signupNameInput.focus();
    });
}

// Paso 1: Iniciar Sesión (Correo y Contraseña)
if (emailCheckForm) {
    emailCheckForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.innerText = '';
        const email = loginEmailInput.value.trim().toLowerCase();
        const loginPasswordInput = document.getElementById('login-password');
        const password = loginPasswordInput ? loginPasswordInput.value.trim() : '';
        if (!email || !password) return;

        // Soporte para activación manual directa (si ingresa ACTV- en el campo de contraseña)
        if (password.startsWith('ACTV-')) {
            try {
                const res = await fetch('/api/activate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: password })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Token de activación inválido o expirado.');
                }
                const data = await res.json();
                if (data.master_key) {
                    masterKey = data.master_key;
                    localStorage.setItem('conny_master_key', masterKey);
                    
                    const config = await apiCall('/config');
                    if (!config.name) {
                        showScreen('onboarding');
                    } else {
                        showScreen('dashboard');
                        initDashboard(config);
                    }
                } else {
                    throw new Error('No se recibió la llave maestra.');
                }
            } catch (err) {
                masterKey = '';
                localStorage.removeItem('conny_master_key');
                loginError.innerText = err.message || 'Token de activación inválido o expirado.';
            }
            return;
        }

        try {
            // Intentar autenticar contra admins
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: email, password: password })
            });

            if (!res.ok) {
                // Fallback robusto: ¿Es el master key directo?
                masterKey = password;
                try {
                    const config = await apiCall('/config');
                    localStorage.setItem('conny_master_key', password);
                    if (!config.name) {
                        showScreen('onboarding');
                    } else {
                        showScreen('dashboard');
                        initDashboard(config);
                    }
                    return;
                } catch (fallbackErr) {
                    masterKey = '';
                    localStorage.removeItem('conny_master_key');
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Credenciales incorrectas');
                }
            }

            const data = await res.json();
            if (data.master_key) {
                masterKey = data.master_key;
                localStorage.setItem('conny_master_key', masterKey);
                
                const config = await apiCall('/config');
                if (!config.name) {
                    showScreen('onboarding');
                } else {
                    showScreen('dashboard');
                    initDashboard(config);
                }
            } else {
                throw new Error('Error de autenticación.');
            }
        } catch (err) {
            loginError.innerText = err.message || 'Error de conexión o credenciales incorrectas.';
        }
    });
}

// Paso 2: Iniciar Sesión (Contraseña o Llave)
if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.innerText = '';
        const password = masterKeyInput.value.trim();
        if (!password) return;

        // Soporte para activación manual directa (si ingresa ACTV- en el campo de contraseña/llave)
        if (password.startsWith('ACTV-')) {
            try {
                const res = await fetch('/api/activate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token: password })
                });
                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Token de activación inválido o expirado.');
                }
                const data = await res.json();
                if (data.master_key) {
                    masterKey = data.master_key;
                    localStorage.setItem('conny_master_key', masterKey);
                    
                    const config = await apiCall('/config');
                    if (!config.name) {
                        showScreen('onboarding');
                    } else {
                        showScreen('dashboard');
                        initDashboard(config);
                    }
                } else {
                    throw new Error('No se recibió la llave maestra.');
                }
            } catch (err) {
                masterKey = '';
                localStorage.removeItem('conny_master_key');
                loginError.innerText = err.message || 'Token de activación inválido o expirado.';
            }
            return;
        }

        try {
            // Intentar autenticar contra admins
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ email: checkedEmail, password: password })
            });

            if (!res.ok) {
                // Fallback robusto: ¿Es el master key directo?
                masterKey = password;
                try {
                    const config = await apiCall('/config');
                    localStorage.setItem('conny_master_key', password);
                    if (!config.name) {
                        showScreen('onboarding');
                    } else {
                        showScreen('dashboard');
                        initDashboard(config);
                    }
                    return;
                } catch (fallbackErr) {
                    masterKey = '';
                    localStorage.removeItem('conny_master_key');
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || 'Credenciales incorrectas o Llave Maestra inválida.');
                }
            }

            const data = await res.json();
            if (data.master_key) {
                masterKey = data.master_key;
                localStorage.setItem('conny_master_key', masterKey);
                
                const config = await apiCall('/config');
                if (!config.name) {
                    showScreen('onboarding');
                } else {
                    showScreen('dashboard');
                    initDashboard(config);
                }
            } else {
                throw new Error('No se recibió la llave maestra.');
            }
        } catch (err) {
            masterKey = '';
            localStorage.removeItem('conny_master_key');
            loginError.innerText = err.message || 'Error al iniciar sesión.';
        }
    });
}

// Paso 3: Completar Onboarding / Registro (Usuario Nuevo)
if (signupForm) {
    signupForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.innerText = '';
        const email = signupEmailInput ? signupEmailInput.value.trim().toLowerCase() : checkedEmail;
        const name = signupNameInput.value.trim();
        const phone = signupPhoneInput.value.trim();
        const specialty = signupSpecialtySelect.value;
        const password = signupPasswordInput.value.trim();
        const token = signupTokenInput.value.trim();

        if (!email || !name || !phone || !specialty || !password || !token) return;

        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    email,
                    password,
                    name,
                    phone,
                    specialty,
                    token
                })
            });

            if (!res.ok) {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Error al completar el registro.');
            }

            const data = await res.json();
            if (data.master_key) {
                // Almacenar temporalmente pero mostrar pantalla de éxito
                masterKey = data.master_key;
                localStorage.setItem('conny_master_key', masterKey);
                
                if (successAccessTokenInput) {
                    successAccessTokenInput.value = masterKey;
                }
                
                if (stepSignupView) stepSignupView.style.display = 'none';
                if (stepSuccessView) stepSuccessView.style.display = 'block';
            } else {
                throw new Error('No se recibió el token de acceso.');
            }
        } catch (err) {
            loginError.innerText = err.message || 'Error de conexión o token inválido.';
        }
    });
}

// Botones de navegación "Atrás"
if (btnBackToEmail) {
    btnBackToEmail.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (stepPasswordView) stepPasswordView.style.display = 'none';
        if (stepEmailView) stepEmailView.style.display = 'block';
        if (loginEmailInput) loginEmailInput.focus();
    });
}

if (btnSignupBack) {
    btnSignupBack.addEventListener('click', (e) => {
        e.preventDefault();
        loginError.innerText = '';
        if (stepSignupView) stepSignupView.style.display = 'none';
        if (stepEmailView) stepEmailView.style.display = 'block';
        if (loginEmailInput) loginEmailInput.focus();
    });
}

// Copiar Token de Acceso
if (btnCopyToken && successAccessTokenInput) {
    btnCopyToken.addEventListener('click', () => {
        successAccessTokenInput.select();
        successAccessTokenInput.setSelectionRange(0, 99999); // Para móviles
        navigator.clipboard.writeText(successAccessTokenInput.value).then(() => {
            const originalText = btnCopyToken.innerText;
            btnCopyToken.innerText = '¡Copiado!';
            btnCopyToken.style.background = '#34a853';
            btnCopyToken.style.color = 'white';
            setTimeout(() => {
                btnCopyToken.innerText = originalText;
                btnCopyToken.style.background = '';
                btnCopyToken.style.color = '';
            }, 1500);
        }).catch(() => {
            alert('No se pudo copiar el token. Cópialo manualmente.');
        });
    });
}

// Botón para ir al Dashboard tras registro
if (btnGoDashboard) {
    btnGoDashboard.addEventListener('click', async () => {
        try {
            const config = await apiCall('/config');
            showScreen('dashboard');
            initDashboard(config);
        } catch (err) {
            loginError.innerText = 'Error al iniciar el Dashboard. Por favor recarga la página.';
        }
    });
}

// Google Onboarding Form Handler
const googleOnboardingForm = document.getElementById('google-onboarding-form');
const onboardingError = document.getElementById('onboarding-error');
if (googleOnboardingForm) {
    googleOnboardingForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        onboardingError.innerText = '';
        
        const name = document.getElementById('gob-owner-name').value.trim();
        const email = document.getElementById('gob-email').value.trim();
        const dob = document.getElementById('gob-dob').value;
        const occupation = document.getElementById('gob-occupation').value.trim();
        let token = document.getElementById('gob-auth-token').value.trim();
        
        if (!token) {
            onboardingError.innerText = 'Por favor, ingresa el token de autorización.';
            return;
        }
        
        if (token.startsWith('ACTV-')) {
            try {
                const res = await fetch('/api/activate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ token })
                });
                if (!res.ok) {
                    const errData = await res.json();
                    throw new Error(errData.detail || 'Token de activación inválido o expirado.');
                }
                const data = await res.json();
                token = data.master_key;
            } catch (err) {
                onboardingError.innerText = err.message;
                return;
            }
        }
        
        masterKey = token;
        try {
            const config = await apiCall('/config');
            localStorage.setItem('conny_master_key', token);
            
            let personaConfig = {};
            if (config.persona_config) {
                try {
                    personaConfig = JSON.parse(config.persona_config);
                } catch(pe) {
                    personaConfig = {};
                }
            }
            personaConfig.owner_dob = dob;
            personaConfig.owner_occupation = occupation;
            
            const patchData = {
                name: name,
                email: email,
                persona_config: personaConfig,
                setup_done: 1
            };
            
            if (window.googleAvatarUrl) {
                patchData.avatar = window.googleAvatarUrl;
            }
            
            await apiCall('/config', 'PATCH', patchData);
            
            if (window.googleAvatarUrl) {
                updateAvatarImages(window.googleAvatarUrl);
            }
            
            history.pushState({}, '', '/chats');
            showScreen('dashboard');
            initDashboard(Object.assign({}, config, patchData));
        } catch (err) {
            masterKey = '';
            localStorage.removeItem('conny_master_key');
            onboardingError.innerText = 'Token de autorización inválido o error al guardar. Verifica con Kikimika AI.';
        }
    });
}

// Kikimika AI Token Modal Logic
const btnRequestToken = document.getElementById('btn-request-token');
const kikimikaModal = document.getElementById('kikimika-modal');
const closeKikimikaModal = document.getElementById('close-kikimika-modal');
const btnSendKikimikaRequest = document.getElementById('btn-send-kikimika-request');
const btnCancelKikimikaRequest = document.getElementById('btn-cancel-kikimika-request');
const kikimikaSuccessMsg = document.getElementById('kikimika-success-msg');

if (btnRequestToken && kikimikaModal) {
    btnRequestToken.addEventListener('click', (e) => {
        e.preventDefault();
        kikimikaModal.classList.add('active');
        kikimikaSuccessMsg.style.display = 'none';
        btnSendKikimikaRequest.style.display = 'block';
    });
    
    closeKikimikaModal.addEventListener('click', () => {
        kikimikaModal.classList.remove('active');
    });
    
    btnCancelKikimikaRequest.addEventListener('click', () => {
        kikimikaModal.classList.remove('active');
    });
    
    btnSendKikimikaRequest.addEventListener('click', async () => {
        btnSendKikimikaRequest.innerText = 'Enviando...';
        btnSendKikimikaRequest.disabled = true;
        
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        btnSendKikimikaRequest.style.display = 'none';
        btnSendKikimikaRequest.innerText = 'Enviar Solicitud';
        btnSendKikimikaRequest.disabled = false;
        kikimikaSuccessMsg.style.display = 'block';
        
        setTimeout(() => {
            kikimikaModal.classList.remove('active');
        }, 2500);
    });
}

// ── Onboarding Handlers ──
    if (onboardingForm) onboardingForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = obClinicNameInput.value.trim();
    const phone = obClinicPhoneInput.value.trim();
    const sector = obSectorSelect.value;
    const servicesText = obServicesInput.value.trim();
    
    const services = servicesText ? servicesText.split(',').map(s => s.trim()) : [];

    try {
        await apiCall('/config', 'PATCH', {
            name,
            phone,
            sector,
            services
        });
        showScreen('dashboard');
        initDashboard();
    } catch (err) {
        alert('Error guardando configuración inicial: ' + err.message);
    }
});

// ── Dashboard Navigation ──
navItems.forEach(item => {
    item.addEventListener('click', () => {
        const targetView = item.dataset.view;
        switchView(targetView);
    });
});

function switchView(viewId) {
    activeTab = viewId;
    navItems.forEach(item => {
        item.classList.remove('active');
        if (item.dataset.view === viewId) {
            item.classList.add('active');
        }
    });

    tabViews.forEach(view => {
        view.classList.remove('active');
    });
    document.getElementById(`view-${viewId}`).classList.add('active');

    // Load data for specific view
    if (viewId === 'chats') {
        loadChatsList();
    } else if (viewId === 'appointments') {
        loadAppointmentsList();
    } else if (viewId === 'account') {
        loadAccountInfo();
    }
}

// ── Dashboard Init ──
function initDashboard(config = null) {
    switchView('chats');
    loadAccountInfo(config);
    showDevBadge();
    // Start periodic update of chats list
    setInterval(() => {
        if (activeTab === 'chats') {
            loadChatsList(false); // background reload without clearing selected state
        }
    }, 10000);
}

// ── Chats / WhatsApp View ──
let allPatients = [];
async function loadChatsList(showLoading = true) {
    try {
        const res = await apiCall('/patients');
        allPatients = res.patients || [];
        renderChatsList(allPatients);
    } catch (err) {
        console.error('Error cargando chats:', err);
    }
}

function renderChatsList(patients) {
    const searchVal = chatSearch.value.toLowerCase();
    const filtered = patients.filter(p => 
        (p.name || '').toLowerCase().includes(searchVal) ||
        (p.phone || '').toLowerCase().includes(searchVal) ||
        (p.chat_id || '').toLowerCase().includes(searchVal)
    );

    chatsList.innerHTML = '';
    if (filtered.length === 0) {
        chatsList.innerHTML = `<div class="empty-state" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; gap: 12px;">
            <svg viewBox="0 0 24 24" style="width: 32px; height: 32px; fill: white; opacity: 0.2;"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg>
            <div style="font-size: 0.75rem; opacity: 0.3; color: white;">Sin conversaciones aún</div>
        </div>`;
        return;
    }

    filtered.forEach(p => {
        const isSelected = selectedChatId === p.chat_id;
        const div = document.createElement('div');
        div.className = `conversation-item ${isSelected ? 'active' : ''}`;
        
        // Format time
        let timeStr = '';
        if (p.last_seen) {
            const date = new Date(p.last_seen);
            timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        div.innerHTML = `
            <div class="item-avatar">
                <svg viewBox="0 0 24 24" class="avatar-svg"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
            </div>
            <div class="item-details">
                <div class="item-header">
                    <span class="item-name">${p.name || p.phone || 'Paciente'}</span>
                    <span class="item-time">${timeStr}</span>
                </div>
                <div class="item-body">
                    <span class="item-msg-snippet">${p.last_message ? (p.last_message_role === 'assistant' ? 'Conny: ' : '') + p.last_message : p.chat_id}</span>
                    <span class="badge-unread" style="display: ${p.visits > 0 ? 'inline' : 'none'}">${p.visits}</span>
                </div>
            </div>
        `;

        div.addEventListener('click', () => selectChat(p));
        chatsList.appendChild(div);
    });
}

if (chatSearch) chatSearch.addEventListener('input', () => {
    renderChatsList(allPatients);
});

function selectChat(patient) {
    selectedChatId = patient.chat_id;
    activeRecipientName.innerText = patient.name || 'Paciente';
    activeRecipientPhone.innerText = patient.phone || patient.chat_id;

    // Highlight active item
    const items = document.querySelectorAll('.conversation-item');
    items.forEach(el => el.classList.remove('active'));
    
    // Toggle views
    chatWelcome.style.display = 'none';
    chatActiveWindow.style.display = 'flex';

    // Highlight in list
    loadChatHistory(patient.chat_id);

    // Setup polling for active chat
    if (chatPollingInterval) {
        clearInterval(chatPollingInterval);
    }
    chatPollingInterval = setInterval(() => {
        if (selectedChatId === patient.chat_id) {
            loadChatHistory(patient.chat_id, false); // silent reload
        }
    }, 3000);
}

let lastMessageCount = 0;
async function loadChatHistory(chatId, scroll = true) {
    try {
        const data = await apiCall(`/conversations/${chatId}`);
        const messages = data.messages || [];
        
        renderMessages(messages);
        
        if (scroll || messages.length !== lastMessageCount) {
            scrollToBottom();
            lastMessageCount = messages.length;
        }
    } catch (err) {
        console.error('Error cargando historial de chat:', err);
    }
}

function renderMessages(messages) {
    messagesScroller.innerHTML = '';
    messages.forEach(msg => {
        const div = document.createElement('div');
        // Role mapping: Conny (sent by assistant/system) is sent. User is received.
        const isSent = msg.role === 'assistant' || msg.role === 'system';
        div.className = `message ${isSent ? 'sent' : 'received'}`;

        let timestampStr = '';
        if (msg.ts) {
            const date = new Date(msg.ts);
            timestampStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        div.innerHTML = `
            <div class="message-content">
                <span>${escapeHtml(msg.content)}</span>
                <div class="message-meta">
                    <span>${timestampStr}</span>
                    ${isSent ? '<svg viewBox="0 0 16 15" width="16" height="15" fill="#53bdeb"><path d="M15.01 3.3L8.07 11.59l-3.8-3.87-.79.79 4.59 4.59L15.8 4.09l-.79-.79z"/></svg>' : ''}
                </div>
            </div>
        `;
        messagesScroller.appendChild(div);
    });
}

function scrollToBottom() {
    messagesScroller.scrollTop = messagesScroller.scrollHeight;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}

// Send Admin direct message to WhatsApp
if (chatSendForm) chatSendForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = chatInputMessage.value.trim();
    if (!text || !selectedChatId) return;

    chatInputMessage.value = '';
    try {
        await apiCall('/send-message', 'POST', {
            chat_id: selectedChatId,
            message: text,
            confirmar: true
        });
        loadChatHistory(selectedChatId);
    } catch (err) {
        alert('Error al enviar mensaje: ' + err.message);
    }
});

// ── Appointments View ──
async function loadAppointmentsList() {
    try {
        const res = await apiCall('/appointments');
        const list = res.appointments || [];
        renderAppointments(list);
    } catch (err) {
        console.error('Error cargando citas:', err);
    }
}

function renderAppointments(list) {
    appointmentsTbody.innerHTML = '';
    if (list.length === 0) {
        appointmentsEmpty.style.display = 'flex';
        return;
    }

    appointmentsEmpty.style.display = 'none';
    list.forEach(apt => {
        const tr = document.createElement('tr');
        
        let dateStr = '-';
        let timeStr = '-';
        if (apt.datetime_slot) {
            const date = new Date(apt.datetime_slot);
            dateStr = date.toLocaleDateString();
            timeStr = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        }

        let badgeClass = 'badge-warning';
        if (apt.status === 'confirmada') badgeClass = 'badge-success';
        if (apt.status === 'cancelada') badgeClass = 'badge-danger';

        tr.innerHTML = `
            <td><strong>${apt.patient_name || 'Paciente sin nombre'}</strong><br><small style="color:var(--text-muted)">${apt.patient_phone || apt.chat_id}</small></td>
            <td>${apt.service || 'Servicio general'}</td>
            <td>${dateStr}</td>
            <td>${timeStr}</td>
            <td><span class="badge ${badgeClass}">${apt.status}</span></td>
            <td>WhatsApp</td>
        `;
        appointmentsTbody.appendChild(tr);
    });
}

// ── Account View ──
async function loadAccountInfo(config = null) {
    try {
        if (!config) {
            config = await apiCall('/config');
        }
        if (profileClinicName) profileClinicName.innerText = config.name || 'Clínica Dental';
        if (profileClinicPhone) profileClinicPhone.innerText = `Teléfono: ${config.phone || '-'}`;
        if (clinicInitials) {
            clinicInitials.innerText = (config.name || 'C').substring(0, 1).toUpperCase();
        }
        
        if (typeof updateAvatarImages === 'function') {
            if (config.avatar) {
                updateAvatarImages(config.avatar);
            } else {
                updateAvatarImages('https://api.dicebear.com/7.x/notionists/svg?seed=Admin&backgroundColor=e2e8f0');
            }
        }

        // Render services list
        if (profileServicesList) {
            profileServicesList.innerHTML = '';
            const services = config.services || [];
            if (services.length === 0) {
                profileServicesList.innerHTML = '<li>No hay servicios definidos</li>';
            } else {
                services.forEach(s => {
                    const li = document.createElement('li');
                    li.innerText = s;
                    profileServicesList.appendChild(li);
                });
            }
        }

        // Get calendar bridge status
        const calStatus = await apiCall('/agenda/status');
        if (calendarStatusBadge) {
            if (calStatus.has_google_calendar) {
                calendarStatusBadge.className = 'badge badge-success';
                calendarStatusBadge.innerText = 'Google Calendar Conectado';
            } else {
                calendarStatusBadge.className = 'badge badge-danger';
                calendarStatusBadge.innerText = 'Desconectado';
            }
        }
    } catch (err) {
        console.error('Error cargando información de cuenta:', err);
    }
}

// ── Admin Chat/Playground ──
if (adminChatForm) adminChatForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const text = adminChatInput.value.trim();
    if (!text) return;

    adminChatInput.value = '';
    
    // Add user bubble to Admin console
    appendAdminBubble('user', text);
    
    try {
        const res = await apiCall('/test', 'POST', {
            message: text,
            user_id: 'admin_playground'
        });
        const bubbles = res.bubbles || [];
        if (bubbles.length > 0) {
            bubbles.forEach(b => appendAdminBubble('conny', b));
        } else {
            appendAdminBubble('conny', res.response || '(sin respuesta)');
        }
    } catch (err) {
        appendAdminBubble('system', 'Error: ' + err.message);
    }
});

function appendAdminBubble(sender, content) {
    const div = document.createElement('div');
    if (sender === 'user') {
        div.className = 'gpt-message gpt-user';
        div.innerHTML = `
            <div class="gpt-content">
                <div class="gpt-text">${escapeHtml(content)}</div>
            </div>
        `;
    } else if (sender === 'conny') {
        div.className = 'gpt-message gpt-ai';
        // Formatear markdown básico (negritas y saltos de línea) si es necesario, 
        // pero escapeHtml asegura texto plano por defecto.
        let formattedContent = escapeHtml(content);
        // Permitir saltos de línea y negritas básicas
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        formattedContent = formattedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formattedContent = formattedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        div.innerHTML = `
            <div class="gpt-avatar">
                <svg viewBox="0 0 24 24" width="20" height="20" fill="currentColor"><path d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"/></svg>
            </div>
            <div class="gpt-content">
                <div class="gpt-text">${formattedContent}</div>
            </div>
        `;
    } else {
        div.className = 'gpt-message gpt-system';
        div.style.justifyContent = 'center';
        div.innerHTML = `
            <div class="gpt-content" style="background:transparent; color:var(--text-muted); font-size:13px; font-style:italic; padding: 4px;">
                ${escapeHtml(content)}
            </div>
        `;
    }
    adminChatMessages.appendChild(div);
    // Smooth scroll al fondo
    adminChatMessages.scrollTo({
        top: adminChatMessages.scrollHeight,
        behavior: 'smooth'
    });
}

// ── Settings Modal ──
if (openSettingsBtn) {
    openSettingsBtn.addEventListener('click', async () => {
        try {
            const config = await apiCall('/config');
            settingsClinicName.value = config.name || '';
            settingsSector.value = config.sector || 'dental';
            
            // Fetch demo status
            const demoStatus = await apiCall('/demo/status').catch(() => ({ demo_mode: true }));
            settingsDemoMode.value = demoStatus.demo_mode ? 'true' : 'false';

            settingsModal.classList.add('active');
        } catch (err) {
            alert('Error cargando configuraciones: ' + err.message);
        }
    });
}

const logoutBtn = document.getElementById('logout-btn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', handleLogout);
}

if (closeSettingsModal) closeSettingsModal.addEventListener('click', () => {
    settingsModal.classList.remove('active');
});

window.addEventListener('click', (e) => {
    if (e.target === settingsModal) {
        settingsModal.classList.remove('active');
    }
});

if (settingsForm) settingsForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = settingsClinicName.value.trim();
    const sector = settingsSector.value;
    const isDemo = settingsDemoMode.value === 'true';

    try {
        await apiCall('/config', 'PATCH', {
            name,
            sector
        });
        
        // Update demo mode
        await apiCall('/demo/activate', 'POST', {
            activate: isDemo
        }).catch(() => {}); // handle if endpoint not present

        settingsModal.classList.remove('active');
        if (activeTab === 'account') {
            loadAccountInfo();
        }
        alert('Configuración guardada exitosamente.');
    } catch (err) {
        alert('Error al guardar configuración: ' + err.message);
    }
});

// Avatar Modal & Upload Logic
const avatarModal = document.getElementById('avatar-modal');
const btnChangePhoto = document.getElementById('btn-change-photo');
const closeAvatarModal = document.getElementById('close-avatar-modal');
const avatarGrid = document.getElementById('avatar-grid');
const fileInput = document.getElementById('avatar-file-input');

function updateAvatarImages(url) {
    if (url) {
        localStorage.setItem('conny_avatar_url', url);
    } else {
        localStorage.removeItem('conny_avatar_url');
    }
    const lgImg = document.getElementById('account-large-image');
    const sbImg = document.getElementById('sidebar-avatar-img');
    const busterUrl = url ? (url.includes('?') ? `${url}&t=${Date.now()}` : `${url}?t=${Date.now()}`) : '';
    if(lgImg) lgImg.src = busterUrl;
    if(sbImg) sbImg.src = busterUrl;
}

if (btnChangePhoto && avatarModal) {
    btnChangePhoto.addEventListener('click', () => {
        avatarModal.classList.add('active');
        if (avatarGrid.children.length === 0) {
            for (let i = 1; i <= 30; i++) {
                const num = i.toString().padStart(2, '0');
                const src = `/static/avatars/avatar_${num}.svg`;
                
                const div = document.createElement('div');
                div.className = 'avatar-item';
                div.onclick = async () => {
                    document.querySelectorAll('.avatar-item').forEach(el => el.classList.remove('selected'));
                    div.classList.add('selected');
                    try {
                        await apiCall('/config', 'PATCH', { avatar: src });
                        updateAvatarImages(src);
                        setTimeout(() => avatarModal.classList.remove('active'), 300);
                    } catch (e) {
                        alert('Error al guardar avatar: ' + e.message);
                    }
                };
                
                const img = document.createElement('img');
                img.src = src;
                
                div.appendChild(img);
                avatarGrid.appendChild(div);
            }
        }
    });

    closeAvatarModal.addEventListener('click', () => {
        avatarModal.classList.remove('active');
    });
}

if (fileInput) {
    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;
        
        if (file.size > 2 * 1024 * 1024) {
            alert("El archivo es muy pesado (Máx 2MB)");
            return;
        }
        
        const reader = new FileReader();
        reader.onload = async (ev) => {
            const base64Str = ev.target.result;
            try {
                const resp = await apiCall('/upload-avatar', 'POST', {
                    filename: file.name,
                    content_type: file.type,
                    data: base64Str
                });
                if (resp.url) {
                    await apiCall('/config', 'PATCH', { avatar: resp.url });
                    updateAvatarImages(resp.url);
                    avatarModal.classList.remove('active');
                }
            } catch (err) {
                alert('Error al subir foto: ' + err.message);
            }
        };
        reader.readAsDataURL(file);
    });
}

// Run Init
checkAuthAndSetup();

// ── Dev Console Logic ──

async function loadDevInstances() {
    try {
        const res = await fetch('/api/dev/instances', {
            headers: { 'X-Master-Key': masterKey }
        });
        if (!res.ok) throw new Error('Error cargando instancias');
        const data = await res.json();
        
        // Render Table
        if (devInstancesTbody) {
            devInstancesTbody.innerHTML = '';
            data.instances.forEach(inst => {
                const tr = document.createElement('tr');
                tr.style.borderBottom = '1px solid rgba(139, 92, 246, 0.1)';
                tr.innerHTML = `
                    <td style="padding: 12px 16px; font-size: 13px; color: #f3f4f6;">
                        <div style="font-weight: 600;">${inst.name}</div>
                        <div style="font-size: 11px; color: #a78bfa;">${inst.sector || 'Desconocido'}</div>
                    </td>
                    <td style="padding: 12px 16px; font-size: 13px; color: #f3f4f6; font-family: monospace;">${inst.port || 'N/A'}</td>
                    <td style="padding: 12px 16px; font-size: 13px;">
                        <span class="${inst.status === 'online' ? 'status-glow-online' : 'status-glow-offline'}" style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; text-transform: uppercase;">
                            <span style="width: 6px; height: 6px; border-radius: 50%; background: currentColor;"></span>
                            ${inst.status}
                        </span>
                    </td>
                    <td style="padding: 12px 16px; font-size: 12px; color: #a78bfa;">${inst.model || 'Por defecto'}</td>
                    <td style="padding: 12px 16px; text-align: right;">
                        <div style="display: flex; gap: 8px; justify-content: flex-end;">
                            <button onclick="handleDevAction('${inst.name}', 'restart')" style="padding: 6px 10px; font-size: 11px; border-radius: 4px; background: rgba(139, 92, 246, 0.15); border: 1px solid rgba(139, 92, 246, 0.3); color: #c084fc; cursor: pointer;">Reiniciar</button>
                            ${inst.status === 'online' ? 
                                `<button onclick="handleDevAction('${inst.name}', 'stop')" style="padding: 6px 10px; font-size: 11px; border-radius: 4px; background: rgba(239, 68, 68, 0.15); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; cursor: pointer;">Detener</button>` : 
                                `<button onclick="handleDevAction('${inst.name}', 'start')" style="padding: 6px 10px; font-size: 11px; border-radius: 4px; background: rgba(16, 185, 129, 0.15); border: 1px solid rgba(16, 185, 129, 0.3); color: #34d399; cursor: pointer;">Iniciar</button>`
                            }
                        </div>
                    </td>
                `;
                devInstancesTbody.appendChild(tr);
            });
        }
        
        // Update Selects (if not currently focused/selected to avoid annoyance)
        const updateSelect = (sel) => {
            if (!sel) return;
            const currentVal = sel.value;
            sel.innerHTML = '<option value="">-- Seleccionar --</option>';
            data.instances.forEach(inst => {
                const opt = document.createElement('option');
                opt.value = inst.name;
                opt.text = inst.name;
                sel.appendChild(opt);
            });
            if (currentVal && Array.from(sel.options).some(o => o.value === currentVal)) {
                sel.value = currentVal;
            }
        };
        
        updateSelect(devPromptInstanceSelect);
        updateSelect(devModelInstanceSelect);
        
        if (devLogsInstanceSelect) {
            const currentLogs = devLogsInstanceSelect.value;
            devLogsInstanceSelect.innerHTML = '<option value="conny">Instancia Base (conny.log)</option>';
            data.instances.forEach(inst => {
                const opt = document.createElement('option');
                opt.value = inst.name;
                opt.text = `${inst.name} (${inst.name}-conny.log)`;
                devLogsInstanceSelect.appendChild(opt);
            });
            if (currentLogs && Array.from(devLogsInstanceSelect.options).some(o => o.value === currentLogs)) {
                devLogsInstanceSelect.value = currentLogs;
            }
        }
        
    } catch (err) {
        console.error('Failed to load dev instances:', err);
    }
}

window.handleDevAction = async (name, action) => {
    try {
        const res = await fetch(`/api/dev/instances/${name}/action`, {
            method: 'POST',
            headers: { 
                'Content-Type': 'application/json',
                'X-Master-Key': masterKey
            },
            body: JSON.stringify({ action })
        });
        if (res.ok) {
            setTimeout(loadDevInstances, 1500);
        } else {
            alert('Error ejecutando la acción en ' + name);
        }
    } catch (err) {
        alert('Error de conexión');
    }
};

if (btnRefreshInstances) {
    btnRefreshInstances.addEventListener('click', loadDevInstances);
}

if (devPromptInstanceSelect) {
    devPromptInstanceSelect.addEventListener('change', async () => {
        const name = devPromptInstanceSelect.value;
        if (!name) {
            if (devPromptTextarea) devPromptTextarea.value = '';
            return;
        }
        try {
            if (promptStatusMsg) {
                promptStatusMsg.innerText = 'Cargando...';
                promptStatusMsg.style.color = '#a78bfa';
            }
            const res = await fetch(`/api/dev/instances/${name}/prompt`, {
                headers: { 'X-Master-Key': masterKey }
            });
            const data = await res.json();
            if (res.ok && devPromptTextarea) {
                devPromptTextarea.value = data.prompt || '';
                if (promptStatusMsg) promptStatusMsg.innerText = '';
            } else {
                throw new Error(data.detail || 'Error cargando prompt');
            }
        } catch (err) {
            if (promptStatusMsg) {
                promptStatusMsg.innerText = err.message;
                promptStatusMsg.style.color = '#ef4444';
            }
        }
    });
}

if (btnSavePrompt) {
    btnSavePrompt.addEventListener('click', async () => {
        const name = devPromptInstanceSelect ? devPromptInstanceSelect.value : '';
        const prompt = devPromptTextarea ? devPromptTextarea.value : '';
        if (!name) {
            alert('Selecciona una instancia primero.');
            return;
        }
        try {
            if (promptStatusMsg) {
                promptStatusMsg.innerText = 'Guardando...';
                promptStatusMsg.style.color = '#a78bfa';
            }
            const res = await fetch(`/api/dev/instances/${name}/prompt`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Master-Key': masterKey
                },
                body: JSON.stringify({ prompt })
            });
            if (res.ok) {
                if (promptStatusMsg) {
                    promptStatusMsg.innerText = '¡Guardado en SQLite!';
                    promptStatusMsg.style.color = '#10b981';
                    setTimeout(() => promptStatusMsg.innerText = '', 3000);
                }
            } else {
                throw new Error('Error al guardar');
            }
        } catch (err) {
            if (promptStatusMsg) {
                promptStatusMsg.innerText = err.message;
                promptStatusMsg.style.color = '#ef4444';
            }
        }
    });
}

if (btnApplyModel) {
    btnApplyModel.addEventListener('click', async () => {
        const name = devModelInstanceSelect ? devModelInstanceSelect.value : '';
        const model = devModelSelect ? devModelSelect.value : '';
        if (!name || !model) {
            alert('Selecciona instancia y modelo.');
            return;
        }
        try {
            if (modelStatusMsg) {
                modelStatusMsg.innerText = 'Aplicando...';
                modelStatusMsg.style.color = '#a78bfa';
            }
            const res = await fetch(`/api/dev/instances/${name}/model`, {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Master-Key': masterKey
                },
                body: JSON.stringify({ model })
            });
            if (res.ok) {
                if (modelStatusMsg) {
                    modelStatusMsg.innerText = '¡Modelo aplicado en caliente!';
                    modelStatusMsg.style.color = '#10b981';
                    setTimeout(() => modelStatusMsg.innerText = '', 3000);
                }
                loadDevInstances();
            } else {
                throw new Error('Error al aplicar modelo');
            }
        } catch (err) {
            if (modelStatusMsg) {
                modelStatusMsg.innerText = err.message;
                modelStatusMsg.style.color = '#ef4444';
            }
        }
    });
}

if (devNewInstanceForm) {
    devNewInstanceForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = devNewName.value.trim();
        const sector = devNewSector.value;
        if (!name) return;
        
        try {
            if (newInstanceStatusMsg) {
                newInstanceStatusMsg.innerText = 'Aprovisionando...';
                newInstanceStatusMsg.style.color = '#a78bfa';
            }
            const res = await fetch('/api/dev/instances/new', {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-Master-Key': masterKey
                },
                body: JSON.stringify({ name, sector })
            });
            if (res.ok) {
                if (newInstanceStatusMsg) {
                    newInstanceStatusMsg.innerText = '¡Instancia creada y arrancando!';
                    newInstanceStatusMsg.style.color = '#10b981';
                    setTimeout(() => newInstanceStatusMsg.innerText = '', 3000);
                }
                devNewName.value = '';
                setTimeout(loadDevInstances, 2000);
            } else {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Error al crear instancia');
            }
        } catch (err) {
            if (newInstanceStatusMsg) {
                newInstanceStatusMsg.innerText = err.message;
                newInstanceStatusMsg.style.color = '#ef4444';
            }
        }
    });
}

async function fetchDevLogs() {
    if (localStorage.getItem('conny_dev_mode') !== 'true') return;
    if (activeTab !== 'dev-console') return;
    
    const name = devLogsInstanceSelect ? devLogsInstanceSelect.value : 'conny';
    try {
        const res = await fetch(`/api/dev/instances/${name}/logs`, {
            headers: { 'X-Master-Key': masterKey }
        });
        if (res.ok) {
            const data = await res.json();
            if (devTerminalLogs) {
                const isScrolledToBottom = devTerminalLogs.scrollHeight - devTerminalLogs.clientHeight <= devTerminalLogs.scrollTop + 50;
                devTerminalLogs.innerText = data.logs;
                if (isScrolledToBottom) {
                    devTerminalLogs.scrollTop = devTerminalLogs.scrollHeight;
                }
            }
        }
    } catch (err) {
        // Silently ignore log fetch errors
    }
}

let logsPollingInterval = null;

if (navDevConsoleBtn) {
    navDevConsoleBtn.addEventListener('click', () => {
        activeTab = 'dev-console';
        tabViews.forEach(v => v.classList.remove('active'));
        if (viewDevConsole) viewDevConsole.classList.add('active');
        
        loadDevInstances();
        
        if (logsPollingInterval) clearInterval(logsPollingInterval);
        logsPollingInterval = setInterval(fetchDevLogs, 3000);
        fetchDevLogs();
    });
}

// Intercept chat/etc tabs to stop log polling
navItems.forEach(item => {
    item.addEventListener('click', () => {
        if (item.dataset.view !== 'dev-console') {
            if (logsPollingInterval) {
                clearInterval(logsPollingInterval);
                logsPollingInterval = null;
            }
        }
    });
});


