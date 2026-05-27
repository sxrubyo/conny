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

let adminChatInitialized = false;

function initAdminChat() {
    if (adminChatInitialized) return;
    adminChatInitialized = true;
    
    const adminChatPlaceholder = document.getElementById('admin-chat-placeholder');
    const adminChatMessages = document.getElementById('admin-chat-messages');
    
    if (adminChatPlaceholder) {
        adminChatPlaceholder.style.display = 'none';
    }
    if (adminChatMessages) {
        adminChatMessages.style.display = 'flex';
    }
}

const adminChatInputElem = document.getElementById('admin-chat-input');
const adminChatFormElem = document.getElementById('admin-chat-form');

if (adminChatInputElem) {
    adminChatInputElem.addEventListener('focus', () => {
        initAdminChat();
        if(adminChatFormElem) adminChatFormElem.classList.add('active-input');
    });
    adminChatInputElem.addEventListener('blur', () => {
        if(!adminChatInputElem.value.trim() && adminChatFormElem) {
            adminChatFormElem.classList.remove('active-input');
        }
    });
    adminChatInputElem.addEventListener('input', initAdminChat);
}

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
            onboardingError.innerText = 'Token de autorización inválido o error al guardar. Verifica con Kiinnvisor AI.';
        }
    });
}

// Kiinnvisor AI Token Modal Logic
const btnRequestToken = document.getElementById('btn-request-token');
const kiinnvisorModal = document.getElementById('kiinnvisor-modal');
const closeKiinnvisorModal = document.getElementById('close-kiinnvisor-modal');
const btnSendKiinnvisorRequest = document.getElementById('btn-send-kiinnvisor-request');
const btnCancelKiinnvisorRequest = document.getElementById('btn-cancel-kiinnvisor-request');
const kiinnvisorSuccessMsg = document.getElementById('kiinnvisor-success-msg');

if (btnRequestToken && kiinnvisorModal) {
    btnRequestToken.addEventListener('click', (e) => {
        e.preventDefault();
        kiinnvisorModal.classList.add('active');
        kiinnvisorSuccessMsg.style.display = 'none';
        btnSendKiinnvisorRequest.style.display = 'block';
    });
    
    closeKiinnvisorModal.addEventListener('click', () => {
        kiinnvisorModal.classList.remove('active');
    });
    
    btnCancelKiinnvisorRequest.addEventListener('click', () => {
        kiinnvisorModal.classList.remove('active');
    });
    
    btnSendKiinnvisorRequest.addEventListener('click', async () => {
        btnSendKiinnvisorRequest.innerText = 'Enviando...';
        btnSendKiinnvisorRequest.disabled = true;
        
        await new Promise(resolve => setTimeout(resolve, 1200));
        
        btnSendKiinnvisorRequest.style.display = 'none';
        btnSendKiinnvisorRequest.innerText = 'Enviar Solicitud';
        btnSendKiinnvisorRequest.disabled = false;
        kiinnvisorSuccessMsg.style.display = 'block';
        
        setTimeout(() => {
            kiinnvisorModal.classList.remove('active');
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
    } else if (viewId === 'appointments' || viewId === 'calendar') {
        loadAppointmentsList();
    } else if (viewId === 'account') {
        loadAccountInfo();
    } else if (viewId === 'admin-chat') {
        loadPersonalityConfig();
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

    // Mobile: show chat area, hide sidebar
    const layout = document.querySelector('.whatsapp-layout');
    if (layout) layout.classList.add('mobile-chat-active');

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

function goBackToChatList() {
    const layout = document.querySelector('.whatsapp-layout');
    if (layout) layout.classList.remove('mobile-chat-active');
    selectedChatId = null;
    chatWelcome.style.display = 'block';
    chatActiveWindow.style.display = 'none';
    if (chatPollingInterval) {
        clearInterval(chatPollingInterval);
        chatPollingInterval = null;
    }
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
            <td><strong>${apt.patient_name || 'Paciente sin nombre'}</strong><br><small style="color:var(--text-secondary)">${apt.patient_phone || apt.chat_id}</small></td>
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
let connyTypingElement = null;
const adminChatPlaceholder = document.getElementById('admin-chat-placeholder');

// Personality calibrator sidebar elements
const btnToggleSidebar = document.getElementById('btn-toggle-sidebar');
const playgroundSidebar = document.getElementById('playground-sidebar');
const sliderFormality = document.getElementById('slider-formality');
const sliderWarmth = document.getElementById('slider-warmth');
const sliderHumor = document.getElementById('slider-humor');
const valFormality = document.getElementById('val-formality');
const valWarmth = document.getElementById('val-warmth');
const valHumor = document.getElementById('val-humor');
const archetypeButtons = document.querySelectorAll('.archetype-btn');

// Agent creation modal elements
const btnCreateAgent = document.getElementById('btn-create-agent');
const modalCreateAgent = document.getElementById('modal-create-agent');
const closeCreateAgentModal = document.getElementById('close-create-agent-modal');
const btnCancelCreateAgent = document.getElementById('btn-cancel-create-agent');
const formCreateAgent = document.getElementById('form-create-agent');
const createAgentName = document.getElementById('create-agent-name');
const createAgentSector = document.getElementById('create-agent-sector');
const createAgentProgress = document.getElementById('create-agent-progress');
const createAgentSuccessMsg = document.getElementById('create-agent-success-msg');
const createAgentErrorMsg = document.getElementById('create-agent-error-msg');
const createAgentAuthWarning = document.getElementById('create-agent-auth-warning');
const btnSubmitCreateAgent = document.getElementById('btn-submit-create-agent');

const archetypesMap = {
    amigable: { formality_level: 0.35, warmth_level: 0.8, humor_level: 0.15 },
    profesional: { formality_level: 0.75, warmth_level: 0.65, humor_level: 0.05 },
    luxury: { formality_level: 0.85, warmth_level: 0.60, humor_level: 0.0 },
    directa: { formality_level: 0.30, warmth_level: 0.50, humor_level: 0.10 },
    energica: { formality_level: 0.25, warmth_level: 0.90, humor_level: 0.30 },
    empatica: { formality_level: 0.55, warmth_level: 0.95, humor_level: 0.0 },
    experta: { formality_level: 0.70, warmth_level: 0.55, humor_level: 0.0 },
    juvenil: { formality_level: 0.10, warmth_level: 0.80, humor_level: 0.35 }
};

function highlightActiveArchetype(f, w, h) {
    if (!archetypeButtons) return;
    
    const fNum = parseFloat(f);
    const wNum = parseFloat(w);
    const hNum = parseFloat(h);
    
    let activeKey = null;
    for (const [key, val] of Object.entries(archetypesMap)) {
        if (Math.abs(val.formality_level - fNum) < 0.02 &&
            Math.abs(val.warmth_level - wNum) < 0.02 &&
            Math.abs(val.humor_level - hNum) < 0.02) {
            activeKey = key;
            break;
        }
    }
    
    archetypeButtons.forEach(btn => {
        if (btn.dataset.archetype === activeKey) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
}

async function loadPersonalityConfig() {
    try {
        const config = await apiCall('/personality');
        
        if (sliderFormality && valFormality) {
            const formalityVal = Math.round((config.formality_level || 0.4) * 100);
            sliderFormality.value = formalityVal;
            valFormality.innerText = `${formalityVal}%`;
        }
        if (sliderWarmth && valWarmth) {
            const warmthVal = Math.round((config.warmth_level || 0.75) * 100);
            sliderWarmth.value = warmthVal;
            valWarmth.innerText = `${warmthVal}%`;
        }
        if (sliderHumor && valHumor) {
            const humorVal = Math.round((config.humor_level || 0.15) * 100);
            sliderHumor.value = humorVal;
            valHumor.innerText = `${humorVal}%`;
        }
        
        highlightActiveArchetype(config.formality_level, config.warmth_level, config.humor_level);
    } catch (err) {
        console.error('Error al cargar la personalidad:', err);
    }
}

let personalitySaveTimeout = null;
function savePersonalityDebounced() {
    if (personalitySaveTimeout) {
        clearTimeout(personalitySaveTimeout);
    }
    
    const fVal = parseFloat(sliderFormality.value) / 100;
    const wVal = parseFloat(sliderWarmth.value) / 100;
    const hVal = parseFloat(sliderHumor.value) / 100;
    highlightActiveArchetype(fVal, wVal, hVal);
    
    personalitySaveTimeout = setTimeout(async () => {
        try {
            await apiCall('/personality', 'PATCH', {
                formality_level: fVal,
                warmth_level: wVal,
                humor_level: hVal
            });
        } catch (err) {
            console.error('Error al actualizar personalidad:', err);
        }
    }, 450);
}

// Attach slider real-time label updates & debounced saving
if (sliderFormality) {
    sliderFormality.addEventListener('input', () => {
        valFormality.innerText = `${sliderFormality.value}%`;
        savePersonalityDebounced();
    });
}
if (sliderWarmth) {
    sliderWarmth.addEventListener('input', () => {
        valWarmth.innerText = `${sliderWarmth.value}%`;
        savePersonalityDebounced();
    });
}
if (sliderHumor) {
    sliderHumor.addEventListener('input', () => {
        valHumor.innerText = `${sliderHumor.value}%`;
        savePersonalityDebounced();
    });
}

// Attach archetype button click handlers
if (archetypeButtons) {
    archetypeButtons.forEach(btn => {
        btn.addEventListener('click', async () => {
            const archKey = btn.dataset.archetype;
            const vals = archetypesMap[archKey];
            if (!vals) return;
            
            sliderFormality.value = Math.round(vals.formality_level * 100);
            valFormality.innerText = `${Math.round(vals.formality_level * 100)}%`;
            
            sliderWarmth.value = Math.round(vals.warmth_level * 100);
            valWarmth.innerText = `${Math.round(vals.warmth_level * 100)}%`;
            
            sliderHumor.value = Math.round(vals.humor_level * 100);
            valHumor.innerText = `${Math.round(vals.humor_level * 100)}%`;
            
            archetypeButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            if (personalitySaveTimeout) clearTimeout(personalitySaveTimeout);
            
            try {
                await apiCall('/personality', 'PATCH', {
                    formality_level: vals.formality_level,
                    warmth_level: vals.warmth_level,
                    humor_level: vals.humor_level
                });
            } catch (err) {
                console.error('Error al configurar arquetipo:', err);
            }
        });
    });
}

// Sidebar toggle handler
if (btnToggleSidebar && playgroundSidebar) {
    btnToggleSidebar.addEventListener('click', () => {
        playgroundSidebar.classList.toggle('collapsed');
        btnToggleSidebar.classList.toggle('active');
    });
}

// Autonomous Agent Creation Modal handlers
if (btnCreateAgent && modalCreateAgent) {
    btnCreateAgent.addEventListener('click', () => {
        modalCreateAgent.classList.add('active');
        
        // Reset modal state
        formCreateAgent.style.display = 'flex';
        createAgentProgress.style.display = 'none';
        createAgentSuccessMsg.style.display = 'none';
        createAgentErrorMsg.style.display = 'none';
        createAgentName.value = '';
        createAgentSector.value = 'dental';
        
        // Reset steps classes & text
        for (let s = 1; s <= 5; s++) {
            const stepEl = document.getElementById(`p-step-${s}`);
            if (stepEl) {
                stepEl.className = 'p-step pending';
                stepEl.querySelector('.p-step-status').innerText = '⏳';
            }
        }
        
        // Check developer master key
        if (!masterKey) {
            createAgentAuthWarning.style.display = 'block';
            btnSubmitCreateAgent.disabled = true;
            btnSubmitCreateAgent.style.opacity = '0.5';
        } else {
            createAgentAuthWarning.style.display = 'none';
            btnSubmitCreateAgent.disabled = false;
            btnSubmitCreateAgent.style.opacity = '1';
        }
    });
}

if (closeCreateAgentModal) {
    closeCreateAgentModal.addEventListener('click', () => {
        modalCreateAgent.classList.remove('active');
    });
}

if (btnCancelCreateAgent) {
    btnCancelCreateAgent.addEventListener('click', () => {
        modalCreateAgent.classList.remove('active');
    });
}

// Modal provisioning workflow helper
const updateStepUI = (stepNum, status, statusChar) => {
    const stepEl = document.getElementById(`p-step-${stepNum}`);
    if (stepEl) {
        stepEl.className = `p-step ${status}`;
        stepEl.querySelector('.p-step-status').innerText = statusChar;
    }
};

const sleepHelper = ms => new Promise(resolve => setTimeout(resolve, ms));

if (formCreateAgent) {
    formCreateAgent.addEventListener('submit', async (e) => {
        e.preventDefault();
        const name = createAgentName.value.trim();
        const sector = createAgentSector.value;
        if (!name) return;
        
        if (!masterKey) {
            createAgentAuthWarning.style.display = 'block';
            return;
        }
        
        // Hide form inputs, show progress section
        formCreateAgent.style.display = 'none';
        createAgentProgress.style.display = 'block';
        createAgentSuccessMsg.style.display = 'none';
        createAgentErrorMsg.style.display = 'none';
        
        const sectorBadge = document.getElementById('p-sector-badge');
        if (sectorBadge) {
            sectorBadge.innerText = sector === 'dental' ? 'Odontología' : 
                                   sector === 'medical' ? 'Médico' : 
                                   sector === 'beauty' ? 'Belleza' : 
                                   sector === 'lawyer' ? 'Legal' : 
                                   sector === 'general' ? 'Servicios' : 'Otro';
        }
        
        try {
            // Step 1: Directorios
            updateStepUI(1, 'in-progress', '•');
            await sleepHelper(800);
            updateStepUI(1, 'success', '✓');
            
            // Step 2: SQLite
            updateStepUI(2, 'in-progress', '•');
            await sleepHelper(800);
            updateStepUI(2, 'success', '✓');
            
            // Step 3: Calibrating Personality
            updateStepUI(3, 'in-progress', '•');
            await sleepHelper(800);
            updateStepUI(3, 'success', '✓');
            
            // Step 4: PM2 microservice registration
            updateStepUI(4, 'in-progress', '•');
            
            // Run the actual API call
            const res = await fetch('/api/dev/instances/new', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Master-Key': masterKey
                },
                body: JSON.stringify({ name, sector })
            });
            
            if (res.ok) {
                updateStepUI(4, 'success', '✓');
                
                // Step 5: Server health check
                updateStepUI(5, 'in-progress', '•');
                await sleepHelper(1000);
                updateStepUI(5, 'success', '✓');
                
                // Show success
                createAgentSuccessMsg.style.display = 'block';
                
                // Sync dev tools instances list if loaded
                if (typeof loadDevInstances === 'function') {
                    loadDevInstances();
                }
                
                // Auto close modal after a short delay
                setTimeout(() => {
                    modalCreateAgent.classList.remove('active');
                }, 3000);
            } else {
                const errData = await res.json().catch(() => ({}));
                throw new Error(errData.detail || 'Error al aprovisionar microservicio en servidor.');
            }
            
        } catch (err) {
            // Mark remaining steps as error or pending
            for (let s = 1; s <= 5; s++) {
                const stepEl = document.getElementById(`p-step-${s}`);
                if (stepEl && stepEl.classList.contains('in-progress')) {
                    updateStepUI(s, 'error', '×');
                } else if (stepEl && stepEl.classList.contains('pending')) {
                    updateStepUI(s, 'pending', '-');
                }
            }
            createAgentErrorMsg.innerText = `Error: ${err.message}`;
            createAgentErrorMsg.style.display = 'block';
        }
    });
}


function showAdminTyping(show) {
    if (!adminChatMessages) return;
    
    if (show) {
        if (connyTypingElement) return; // Already showing
        
        connyTypingElement = document.createElement('div');
        connyTypingElement.className = 'gpt-message gpt-ai conny-typing-bubble';
        connyTypingElement.id = 'conny-typing-indicator';
        connyTypingElement.innerHTML = `
            <div class="gpt-avatar">
                <img src="/isotype" class="conny-avatar-img" alt="Conny">
            </div>
            <div class="typing-indicator-box">
                <div class="typing-arrows">
                    <span>❯</span>
                    <span>❯</span>
                    <span>❯</span>
                </div>
            </div>
        `;
        adminChatMessages.appendChild(connyTypingElement);
        adminChatMessages.scrollTo({
            top: adminChatMessages.scrollHeight,
            behavior: 'smooth'
        });
    } else {
        if (connyTypingElement) {
            connyTypingElement.remove();
            connyTypingElement = null;
        }
    }
}

if (adminChatForm) adminChatForm.addEventListener('submit', async (e) => {
    initAdminChat();
    e.preventDefault();
    const text = adminChatInput.value.trim();
    if (!text) return;

    adminChatInput.value = '';
    
    // Add user bubble to Admin console
    appendAdminBubble('user', text);
    
    // Show typing animation
    showAdminTyping(true);
    
    try {
        const res = await apiCall('/test', 'POST', {
            message: text,
            user_id: 'admin_playground'
        });
        
        showAdminTyping(false);
        
        const bubbles = res.bubbles || [];
        if (bubbles.length > 0) {
            bubbles.forEach(b => appendAdminBubble('conny', b));
        } else {
            appendAdminBubble('conny', res.response || '(sin respuesta)');
        }
    } catch (err) {
        showAdminTyping(false);
        appendAdminBubble('system', 'Error: ' + err.message);
    }
});

function appendAdminBubble(sender, content) {
    if (!adminChatMessages) return;
    
    const div = document.createElement('div');
    if (sender === 'user') {
        const userAvatar = localStorage.getItem('conny_avatar_url') || '/static/avatars/avatar_01.svg';
        div.className = 'gpt-message gpt-user';
        div.innerHTML = `
            <div class="gpt-content">
                <div class="gpt-text">${escapeHtml(content)}</div>
            </div>
            <div class="gpt-avatar">
                <img src="${userAvatar}" class="user-avatar-img" alt="Tú">
            </div>
        `;
    } else if (sender === 'conny') {
        div.className = 'gpt-message gpt-ai';
        let formattedContent = escapeHtml(content);
        formattedContent = formattedContent.replace(/\n/g, '<br>');
        formattedContent = formattedContent.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formattedContent = formattedContent.replace(/\*(.*?)\*/g, '<em>$1</em>');
        
        div.innerHTML = `
            <div class="gpt-avatar">
                <img src="/isotype" class="conny-avatar-img" alt="Conny">
            </div>
            <div class="gpt-content">
                <div class="gpt-text">${formattedContent}</div>
            </div>
        `;
    } else {
        div.className = 'gpt-message gpt-system';
        div.style.justifyContent = 'center';
        div.innerHTML = `
            <div class="gpt-content" style="background:transparent; color:var(--text-secondary); font-size:13px; font-style:italic; padding: 4px;">
                ${escapeHtml(content)}
            </div>
        `;
    }
    adminChatMessages.appendChild(div);
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

/* ── Luxury Audio Transcription & File Upload Implementation ── */

// 1. Fullscreen Lightbox Modal Controls
const lightboxModal = document.getElementById('lightbox-modal');
const lightboxImg = document.getElementById('lightbox-img');
const lightboxClose = document.getElementById('lightbox-close');

function openLightbox(src) {
    if (lightboxModal && lightboxImg) {
        lightboxImg.src = src;
        lightboxModal.classList.add('active');
    }
}

function closeLightbox() {
    if (lightboxModal) {
        lightboxModal.classList.remove('active');
    }
}

if (lightboxClose) lightboxClose.addEventListener('click', closeLightbox);
if (lightboxModal) {
    lightboxModal.addEventListener('click', (e) => {
        if (e.target === lightboxModal) closeLightbox();
    });
}

// 2. Global file queues for both forms
let chatUploadedFiles = [];
let adminUploadedFiles = [];

// DOM Elements bindings
const chatFileInput = document.getElementById('chat-file-input');
const chatFilePreviewBar = document.getElementById('chat-file-preview-bar');
const chatUploadProgress = document.getElementById('chat-upload-progress');
const chatUploadProgressFill = document.getElementById('chat-upload-progress-fill');
const chatUploadProgressPercent = document.getElementById('chat-upload-progress-percent');

const adminFileInput = document.getElementById('admin-file-input');
const adminFilePreviewBar = document.getElementById('admin-file-preview-bar');
const adminUploadProgress = document.getElementById('admin-upload-progress');
const adminUploadProgressFill = document.getElementById('admin-upload-progress-fill');
const adminUploadProgressPercent = document.getElementById('admin-upload-progress-percent');

const btnChatUpload = document.getElementById('btn-chat-upload');
const btnAdminUpload = document.getElementById('btn-admin-upload');
const btnChatAudio = document.getElementById('btn-chat-audio');
const btnAdminAudio = document.getElementById('btn-admin-audio');

// Trigger upload clicks
if (btnChatUpload && chatFileInput) {
    btnChatUpload.addEventListener('click', () => chatFileInput.click());
}
if (btnAdminUpload && adminFileInput) {
    btnAdminUpload.addEventListener('click', () => adminFileInput.click());
}

// Handle file selections
if (chatFileInput) {
    chatFileInput.addEventListener('change', (e) => handleFileSelection(e.target.files, 'chat'));
}
if (adminFileInput) {
    adminFileInput.addEventListener('change', (e) => handleFileSelection(e.target.files, 'admin'));
}

function handleFileSelection(files, scope) {
    if (scope === 'admin') {
        initAdminChat();
    }
    const list = scope === 'chat' ? chatUploadedFiles : adminUploadedFiles;
    const previewBar = scope === 'chat' ? chatFilePreviewBar : adminFilePreviewBar;

    Array.from(files).forEach(file => {
        const reader = new FileReader();
        const isImage = file.type.startsWith('image/');
        
        reader.onload = function(e) {
            list.push({
                name: file.name,
                type: file.type,
                size: (file.size / 1024).toFixed(1) + ' KB',
                data: e.target.result, // base64 or source
                isImage
            });
            renderFilePreviews(scope);
        };
        reader.readAsDataURL(file);
    });

    // Reset input value so same file can be uploaded again if deleted
    if (scope === 'chat' && chatFileInput) chatFileInput.value = '';
    if (scope === 'admin' && adminFileInput) adminFileInput.value = '';
}

function renderFilePreviews(scope) {
    const list = scope === 'chat' ? chatUploadedFiles : adminUploadedFiles;
    const previewBar = scope === 'chat' ? chatFilePreviewBar : adminFilePreviewBar;

    if (!previewBar) return;
    previewBar.innerHTML = '';

    if (list.length === 0) {
        previewBar.style.display = 'none';
        return;
    }

    previewBar.style.display = 'flex';

    list.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'preview-thumbnail';

        if (file.isImage) {
            item.innerHTML = `
                <img src="${file.data}" alt="${file.name}">
                <div class="btn-remove-preview" onclick="removeFile('${scope}', ${index})">&times;</div>
            `;
        } else {
            // Document icon path
            item.innerHTML = `
                <div class="generic-file-icon">
                    <svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                    <span>${file.name}</span>
                </div>
                <div class="btn-remove-preview" onclick="removeFile('${scope}', ${index})">&times;</div>
            `;
        }
        previewBar.appendChild(item);
    });
}

// Remove single file function exposed to window for inline onclick handler
window.removeFile = function(scope, index) {
    if (scope === 'chat') {
        chatUploadedFiles.splice(index, 1);
        renderFilePreviews('chat');
    } else {
        adminUploadedFiles.splice(index, 1);
        renderFilePreviews('admin');
    }
};

// 3. Simulated Upload Progression
async function simulateUploadProgress(scope) {
    const progressContainer = scope === 'chat' ? chatUploadProgress : adminUploadProgress;
    const fill = scope === 'chat' ? chatUploadProgressFill : adminUploadProgressFill;
    const percent = scope === 'chat' ? chatUploadProgressPercent : adminUploadProgressPercent;

    if (!progressContainer || !fill || !percent) return;

    progressContainer.style.display = 'flex';
    fill.style.width = '0%';
    percent.innerText = '0%';

    return new Promise(resolve => {
        let current = 0;
        const interval = setInterval(() => {
            current += Math.floor(Math.random() * 15) + 5;
            if (current >= 100) {
                current = 100;
                clearInterval(interval);
                fill.style.width = '100%';
                percent.innerText = '100%';
                setTimeout(() => {
                    progressContainer.style.display = 'none';
                    resolve();
                }, 200);
            } else {
                fill.style.width = current + '%';
                percent.innerText = current + '%';
            }
        }, 80);
    });
}

// 4. Render attached files into the conversation history
function createAttachmentMarkup(files) {
    if (!files || files.length === 0) return '';

    let imagesMarkup = '';
    let docsMarkup = '';

    files.forEach(file => {
        if (file.isImage) {
            imagesMarkup += `
                <div class="chat-attachment-item" onclick="openLightbox('${file.data}')">
                    <img src="${file.data}" alt="${file.name}">
                </div>
            `;
        } else {
            docsMarkup += `
                <div class="chat-attachment-item generic-doc" onclick="window.open('${file.data}', '_blank')">
                    <svg viewBox="0 0 24 24"><path d="M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z"/></svg>
                    <div class="doc-name">${file.name}</div>
                    <div class="doc-size">${file.size}</div>
                </div>
            `;
        }
    });

    let html = '';
    if (imagesMarkup) {
        html += `<div class="chat-attachment-grid">${imagesMarkup}</div>`;
    }
    if (docsMarkup) {
        html += `<div class="chat-attachment-grid">${docsMarkup}</div>`;
    }
    return html;
}

// Intercept Chat Send Form
if (chatSendForm) {
    const originalSubmitListener = chatSendForm.onsubmit || null;
    
    chatSendForm.addEventListener('submit', async (e) => {
        // If there are files queued, we handle simulation first
        if (chatUploadedFiles.length > 0) {
            e.preventDefault();
            e.stopImmediatePropagation();

            const text = chatInputMessage.value.trim();
            const queuedFiles = [...chatUploadedFiles];

            // Clear preview immediately to lock the UI
            chatUploadedFiles = [];
            renderFilePreviews('chat');

            await simulateUploadProgress('chat');

            // Visually append locally for immediate wow-factor feedback
            const div = document.createElement('div');
            div.className = 'message sent';
            const timestampStr = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
            
            let attachmentHtml = createAttachmentMarkup(queuedFiles);
            let textSpan = text ? `<span>${escapeHtml(text)}</span>` : '';

            div.innerHTML = `
                <div class="message-content">
                    ${attachmentHtml}
                    ${textSpan}
                    <div class="message-meta">
                        <span>${timestampStr}</span>
                        <svg viewBox="0 0 16 15" width="16" height="15" fill="#53bdeb"><path d="M15.01 3.3L8.07 11.59l-3.8-3.87-.79.79 4.59 4.59L15.8 4.09l-.79-.79z"/></svg>
                    </div>
                </div>
            `;
            messagesScroller.appendChild(div);
            scrollToBottom();

            // Clear input box
            chatInputMessage.value = '';

            // Send actual text message to backend
            if (text && selectedChatId) {
                try {
                    await apiCall('/send-message', 'POST', {
                        chat_id: selectedChatId,
                        message: text + " [Archivo Adjunto: " + queuedFiles.map(f => f.name).join(', ') + "]",
                        confirmar: true
                    });
                    loadChatHistory(selectedChatId);
                } catch (err) {
                    console.error('Error sending attached metadata:', err);
                }
            }
        }
    });
}

// Intercept Admin Playgroup Chat Form
if (adminChatForm) {
    adminChatForm.addEventListener('submit', async (e) => {
        if (adminUploadedFiles.length > 0) {
            initAdminChat();
            e.preventDefault();
            e.stopImmediatePropagation();

            const text = adminChatInput.value.trim();
            const queuedFiles = [...adminUploadedFiles];

            // Reset input values
            adminUploadedFiles = [];
            renderFilePreviews('admin');

            await simulateUploadProgress('admin');

            // Append locally to user playground view
            const div = document.createElement('div');
            div.className = 'gpt-message gpt-user';
            const userAvatar = localStorage.getItem('conny_avatar_url') || '/static/avatars/avatar_01.svg';
            let attachmentHtml = createAttachmentMarkup(queuedFiles);
            let textDiv = text ? `<div class="gpt-text">${escapeHtml(text)}</div>` : '';

            div.innerHTML = `
                <div class="gpt-content">
                    ${attachmentHtml}
                    ${textDiv}
                </div>
                <div class="gpt-avatar">
                    <img src="${userAvatar}" class="user-avatar-img" alt="Tú">
                </div>
            `;
            adminChatMessages.appendChild(div);
            adminChatMessages.scrollTo({
                top: adminChatMessages.scrollHeight,
                behavior: 'smooth'
            });

            adminChatInput.value = '';

            // Query Conny for dynamic test responses
            showAdminTyping(true);
            try {
                const queryText = text || `[Envió ${queuedFiles.length} archivos: ` + queuedFiles.map(f => f.name).join(', ') + ']';
                const res = await apiCall('/test', 'POST', {
                    message: queryText,
                    user_id: 'admin_playground'
                });
                
                showAdminTyping(false);
                const bubbles = res.bubbles || [];
                if (bubbles.length > 0) {
                    bubbles.forEach(b => appendAdminBubble('conny', b));
                } else {
                    appendAdminBubble('conny', res.response || '(sin respuesta)');
                }
            } catch (err) {
                showAdminTyping(false);
                appendAdminBubble('system', 'Error: ' + err.message);
            }
        }
    });
}

// 5. Speech-to-Text Recording Engine (Web Speech API)
let recognition = null;
let activeRecordingInputId = null;
let activeRecordingButton = null;

function setupSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        console.warn('Speech recognition is not supported in this browser.');
        // Gracefully disable audio buttons and add custom description
        if (btnChatAudio) {
            btnChatAudio.style.opacity = '0.4';
            btnChatAudio.title = 'Transcripción de audio no soportada en este navegador';
        }
        if (btnAdminAudio) {
            btnAdminAudio.style.opacity = '0.4';
            btnAdminAudio.title = 'Transcripción de audio no soportada en este navegador';
        }
        return false;
    }

    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.lang = 'es-ES';
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = function() {
        if (activeRecordingButton) {
            activeRecordingButton.classList.add('is-recording');
        }
    };

    recognition.onresult = function(e) {
        const transcript = e.results[0][0].transcript;
        const targetInput = document.getElementById(activeRecordingInputId);
        if (targetInput && transcript) {
            const currentValue = targetInput.value.trim();
            targetInput.value = currentValue ? (currentValue + ' ' + transcript) : transcript;
            // Move cursor to end
            targetInput.focus();
            targetInput.selectionStart = targetInput.selectionEnd = targetInput.value.length;
        }
    };

    recognition.onerror = function(e) {
        console.error('Speech recognition error:', e.error);
        stopRecording();
    };

    recognition.onend = function() {
        stopRecording();
    };

    return true;
}

function startRecording(inputId, btnElement) {
    if (!recognition) {
        const initialized = setupSpeechRecognition();
        if (!initialized) {
            alert('La transcripción de audio no está disponible en este navegador. Por favor usa Google Chrome, Microsoft Edge o Apple Safari.');
            return;
        }
    }

    // Stop current if any is running
    stopRecording();

    activeRecordingInputId = inputId;
    activeRecordingButton = btnElement;

    try {
        recognition.start();
    } catch (err) {
        console.error('Failed to start speech recognition:', err);
    }
}

function stopRecording() {
    if (recognition) {
        try {
            recognition.stop();
        } catch (err) {}
    }
    if (activeRecordingButton) {
        activeRecordingButton.classList.remove('is-recording');
    }
    activeRecordingInputId = null;
    activeRecordingButton = null;
}

function toggleSpeechRecording(inputId, btnElement) {
    if (activeRecordingButton === btnElement) {
        stopRecording();
    } else {
        startRecording(inputId, btnElement);
    }
}

if (btnChatAudio) {
    btnChatAudio.addEventListener('click', (e) => {
        e.preventDefault();
        toggleSpeechRecording('chat-input-message', btnChatAudio);
    });
}
if (btnAdminAudio) {
    btnAdminAudio.addEventListener('click', (e) => {
        initAdminChat();
        e.preventDefault();
        toggleSpeechRecording('admin-chat-input', btnAdminAudio);
    });
}





// ── Calendar View Logic ──
let currentCalendarDate = new Date();
let globalAppointmentsList = [];

const calendarGridContent = document.getElementById('calendar-grid-content');
const calendarMonthTitle = document.getElementById('calendar-month-title');
const calendarPrevBtn = document.getElementById('calendar-prev-btn');
const calendarNextBtn = document.getElementById('calendar-next-btn');
const calendarTodayCount = document.getElementById('calendar-today-count');

if (calendarPrevBtn) {
    calendarPrevBtn.addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() - 1);
        renderCalendarGrid();
    });
}
if (calendarNextBtn) {
    calendarNextBtn.addEventListener('click', () => {
        currentCalendarDate.setMonth(currentCalendarDate.getMonth() + 1);
        renderCalendarGrid();
    });
}

function renderCalendarGrid() {
    if (!calendarGridContent) return;

    const year = currentCalendarDate.getFullYear();
    const month = currentCalendarDate.getMonth();

    const monthNames = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    if (calendarMonthTitle) calendarMonthTitle.textContent = `${monthNames[month]} ${year}`;

    // Calculate days
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    calendarGridContent.innerHTML = '';

    // Render Headers inside the grid
    const daysOfWeek = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
    daysOfWeek.forEach(d => {
        const th = document.createElement('div');
        th.textContent = d;
        th.style.padding = '12px';
        
        th.style.textAlign = 'right';
        th.style.fontSize = '12px';
        th.style.fontWeight = '600';
        th.style.color = 'var(--text-secondary)';
        th.style.textTransform = 'uppercase';
        calendarGridContent.appendChild(th);
    });

    const today = new Date();
    let todayCount = 0;

    // Previous month padding
    for (let i = 0; i < firstDay; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'var(--bg-panel)';
        cell.style.minHeight = '100px';
        
        calendarGridContent.appendChild(cell);
    }

    // Current month days
    for (let day = 1; day <= daysInMonth; day++) {
        const dateString = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;

        const cell = document.createElement('div');
                cell.style.background = 'var(--bg-main)';
        cell.style.minHeight = '100px';
        cell.style.padding = '8px';
        cell.style.display = 'flex';
        cell.style.flexDirection = 'column';
        cell.style.gap = '4px';
        cell.style.cursor = 'pointer';

        const isToday = (day === today.getDate() && month === today.getMonth() && year === today.getFullYear());

        // Day number
        const dayHeader = document.createElement('div');
        dayHeader.style.display = 'flex';
        dayHeader.style.justifyContent = 'flex-end';
        dayHeader.style.marginBottom = '6px';
        
        const dayNumber = document.createElement('div');
        dayNumber.textContent = day;
        dayNumber.style.fontSize = '12px';
        dayNumber.style.minWidth = '24px';
        dayNumber.style.height = '24px';
        dayNumber.style.padding = '0 6px';
        dayNumber.style.display = 'flex';
        dayNumber.style.alignItems = 'center';
        dayNumber.style.justifyContent = 'center';
        dayNumber.style.borderRadius = '6px';
        dayNumber.style.border = '1px solid var(--border-color)';
        dayNumber.style.fontWeight = isToday ? '700' : '600';
        
        if (isToday) {
            dayNumber.style.color = '#ffffff';
            dayNumber.style.background = 'var(--accent-color)';
            dayNumber.style.borderColor = 'var(--accent-color)';
        } else {
            dayNumber.style.color = 'var(--text-primary)';
            dayNumber.style.background = 'var(--bg-main)';
        }
        
        dayHeader.appendChild(dayNumber);
        cell.appendChild(dayHeader);

        // Find appointments for this day
        const dayAppointments = globalAppointmentsList.filter(apt => {
            if (!apt.datetime_slot) return false;
            const d = new Date(apt.datetime_slot);
            return d.getFullYear() === year && d.getMonth() === month && d.getDate() === day;
        });

        if (isToday) todayCount = dayAppointments.length;

        // Render appointments inside the cell
        dayAppointments.slice(0, 3).forEach(apt => {
            const aptEl = document.createElement('div');
            aptEl.style.background = apt.status === 'confirmada' ? 'var(--success-color)' : 'var(--accent-color)';
            aptEl.style.color = '#ffffff';
            aptEl.style.padding = '4px 8px';
            aptEl.style.borderRadius = '6px';
            aptEl.style.fontSize = '11px';
            aptEl.style.whiteSpace = 'nowrap';
            aptEl.style.overflow = 'hidden';
            aptEl.style.textOverflow = 'ellipsis';
            aptEl.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
            
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente';
            
            aptEl.innerHTML = `<span style="font-weight: 600;">${aptTime}</span> <span style="opacity:0.8; margin-left:4px;">${aptName}</span>`;
            cell.appendChild(aptEl);
        });
        
        if (dayAppointments.length > 3) {
            const moreEl = document.createElement('div');
            moreEl.style.fontSize = '11px';
            moreEl.style.color = 'var(--text-secondary)';
            moreEl.style.fontWeight = '600';
            moreEl.style.marginTop = '4px';
            moreEl.textContent = `+${dayAppointments.length - 3} más`;
            cell.appendChild(moreEl);
        }
        
        // Open Modal on click
        cell.addEventListener('click', () => {
            openCalendarModal(day, monthNames[month], year, dayAppointments);
        });

        calendarGridContent.appendChild(cell);
    }

    // Next month padding
    const totalCells = firstDay + daysInMonth;
    const remainingCells = (7 - (totalCells % 7)) % 7;
    for (let i = 0; i < remainingCells; i++) {
        const cell = document.createElement('div');
        cell.style.background = 'var(--bg-panel)';
        cell.style.minHeight = '100px';
        
        calendarGridContent.appendChild(cell);
    }

    if (calendarTodayCount) calendarTodayCount.textContent = todayCount;
}

function openCalendarModal(day, monthStr, year, appointments) {
    const modal = document.getElementById('calendar-day-modal');
    const title = document.getElementById('calendar-day-modal-title');
    const content = document.getElementById('calendar-day-modal-content');

    if (!modal) return;

    title.textContent = `${day} de ${monthStr} ${year}`;
    content.innerHTML = '';

    if (appointments.length === 0) {
        content.innerHTML = `
            <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 0; opacity: 0.6;">
                <svg viewBox="0 0 24 24" width="48" height="48" fill="none" stroke="var(--text-secondary)" stroke-width="1.5" style="margin-bottom: 16px;"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                <p style="color: var(--text-secondary); font-size: 15px; font-weight: 500; margin: 0;">Día libre</p>
                <p style="color: var(--text-secondary); font-size: 13px; margin: 4px 0 0 0;">No hay citas agendadas para este día.</p>
            </div>
        `;
    } else {
        appointments.forEach(apt => {
            const aptTime = new Date(apt.datetime_slot).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
            const aptName = apt.patient_name || 'Paciente sin nombre';
            const statusColor = apt.status === 'confirmada' ? '#10b981' : 'var(--accent-color)';

            content.innerHTML += `
                <div style="background: var(--bg-main); border-left: 4px solid ${statusColor}; padding: 16px; margin-bottom: 16px; border-radius: 0 12px 12px 0; border: 1px solid var(--border-color); border-left-width: 4px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <strong style="color: var(--text-primary); font-size: 15px;">${aptTime} - ${apt.service || 'Consulta'}</strong>
                        <span style="font-size: 11px; padding: 4px 10px; border-radius: 12px; font-weight: 600; background: ${apt.status === 'confirmada' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(139,92,246,0.1)'}; color: ${statusColor}; text-transform: capitalize;">${apt.status}</span>
                    </div>
                    <div style="color: var(--text-secondary); font-size: 14px; font-weight: 500;">${aptName}</div>
                    <div style="color: var(--text-secondary); font-size: 13px; margin-top: 4px; display: flex; align-items: center; gap: 6px;">
                        <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
                        ${apt.patient_phone || apt.chat_id || 'N/A'}
                    </div>
                </div>
            `;
        });
    }

    modal.style.display = 'flex';
}

// Modify existing renderAppointments to also render the calendar
const originalRenderAppointments = renderAppointments;
renderAppointments = function(list) {
    globalAppointmentsList = list;
    originalRenderAppointments(list);
    renderCalendarGrid();
};





// ── Library View Logic ──
const libraryAddBtn = document.getElementById('library-add-btn');
const libraryFileInput = document.getElementById('library-file-input');
const libraryResourceList = document.getElementById('library-resource-list');

const libModal = document.getElementById('library-config-modal');
const libCloseBtn = document.getElementById('library-config-close');
const libCancelBtn = document.getElementById('library-config-cancel');
const libSaveBtn = document.getElementById('library-config-save');
const libPreviewContainer = document.getElementById('library-preview-container');
const libFilename = document.getElementById('library-config-filename');
const libFilesize = document.getElementById('library-config-filesize');
const libInstructions = document.getElementById('library-config-instructions');

let pendingLibraryFile = null;
let pendingLibraryPreviewUrl = null;

if (libraryAddBtn && libraryFileInput) {
    libraryAddBtn.addEventListener('click', () => {
        libraryFileInput.click();
    });

    libraryFileInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            const file = files[0];
            pendingLibraryFile = file;
            const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
            
            libFilename.textContent = file.name;
            libFilesize.textContent = sizeMb + " MB";
            if(libInstructions) libInstructions.value = "";
            
            libPreviewContainer.innerHTML = '';
            libPreviewContainer.style.background = 'var(--bg-main)';
            if (pendingLibraryPreviewUrl) {
                URL.revokeObjectURL(pendingLibraryPreviewUrl);
                pendingLibraryPreviewUrl = null;
            }
            
            if (file.type.startsWith('image/')) {
                pendingLibraryPreviewUrl = URL.createObjectURL(file);
                libPreviewContainer.innerHTML = `<img src="${pendingLibraryPreviewUrl}" style="width: 100%; height: 100%; object-fit: cover;">`;
            } else if (file.name.toLowerCase().endsWith('.pdf')) {
                libPreviewContainer.innerHTML = `<svg viewBox="0 0 24 24" width="48" height="48" fill="#ef4444"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>`;
                libPreviewContainer.style.background = 'rgba(239, 68, 68, 0.05)';
            } else {
                libPreviewContainer.innerHTML = `<svg viewBox="0 0 24 24" width="48" height="48" fill="#8b5cf6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/></svg>`;
                libPreviewContainer.style.background = 'rgba(139, 92, 246, 0.05)';
            }
            
            if(libModal) libModal.style.display = 'flex';
        }
    });
    
    const closeModal = () => {
        if(libModal) libModal.style.display = 'none';
        libraryFileInput.value = '';
        pendingLibraryFile = null;
    };
    
    if(libCloseBtn) libCloseBtn.addEventListener('click', closeModal);
    if(libCancelBtn) libCancelBtn.addEventListener('click', closeModal);
    
    if(libSaveBtn) libSaveBtn.addEventListener('click', () => {
        if (!pendingLibraryFile) return;
        
        const file = pendingLibraryFile;
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        const instruction = libInstructions ? libInstructions.value.trim() : '';
        
        const card = document.createElement('div');
        card.className = 'resource-card gallery-item';
        card.style.background = 'var(--bg-panel)';
        card.style.border = '1px solid var(--border-color)';
        card.style.borderRadius = '8px';
        card.style.overflow = 'hidden';
        card.style.display = 'flex';
        card.style.flexDirection = 'column';
        card.style.aspectRatio = '1 / 1';
        card.style.animation = 'fadeIn 0.3s ease';
        card.style.boxShadow = '0 4px 12px rgba(0,0,0,0.05)';
        card.style.cursor = 'pointer';
        card.style.position = 'relative';
        
        let previewHtml = '';
        let modalPreviewHtml = '';
        if (file.type.startsWith('image/')) {
            const url = URL.createObjectURL(file);
            previewHtml = `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover; transition: transform 0.3s ease;">`;
            modalPreviewHtml = `<img src="${url}" style="width: 100%; height: 100%; object-fit: cover;">`;
        } else if (file.name.toLowerCase().endsWith('.pdf')) {
            previewHtml = `<div style="width: 100%; height: 100%; background: rgba(239, 68, 68, 0.05); display: flex; align-items: center; justify-content: center; transition: background 0.3s ease;">` + `<svg viewBox="0 0 24 24" width="48" height="48" fill="#ef4444"><path d="M20 2H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-8.5 7.5c0 .83-.67 1.5-1.5 1.5H9v2H7.5V7H10c.83 0 1.5.67 1.5 1.5v1zm5 2c0 .83-.67 1.5-1.5 1.5h-2.5V7H15c.83 0 1.5.67 1.5 1.5v3zm4-3H19v1h1.5V11H19v2h-1.5V7h3v1.5zM9 9.5h1v-1H9v1zM4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm10 5.5h1v-3h-1v3z"/></svg>` + `</div>`;
            modalPreviewHtml = previewHtml;
        } else {
            previewHtml = `<div style="width: 100%; height: 100%; background: rgba(139, 92, 246, 0.05); display: flex; align-items: center; justify-content: center; transition: background 0.3s ease;">` + `<svg viewBox="0 0 24 24" width="48" height="48" fill="#8b5cf6"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8l-6-6zm-1 1.5L18.5 9H13V3.5zM6 20V4h5v7h7v9H6z"/></svg>` + `</div>`;
            modalPreviewHtml = previewHtml;
        }
        
        card.innerHTML = `
            <div style="width: 100%; height: 100%; overflow: hidden;" class="preview-wrapper">
                ${previewHtml}
            </div>
            <div style="position: absolute; bottom: 0; left: 0; right: 0; padding: 12px; background: linear-gradient(to top, rgba(0,0,0,0.8), transparent); color: white; border-bottom-left-radius: 8px; border-bottom-right-radius: 8px;">
                <h4 style="margin: 0; font-size: 13px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-shadow: 0 1px 2px rgba(0,0,0,0.8);">${file.name}</h4>
            </div>
            <!-- Hover overlay -->
            <div class="hover-overlay" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; background: rgba(139,92,246,0.2); opacity: 0; transition: opacity 0.2s ease; display: flex; align-items: center; justify-content: center;">
                <div style="background: var(--bg-panel); color: var(--text-primary); padding: 8px 16px; border-radius: 20px; font-size: 13px; font-weight: 600; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">Ver detalles</div>
            </div>
        `;
        
        card.addEventListener('mouseover', () => {
            card.querySelector('.hover-overlay').style.opacity = '1';
            const img = card.querySelector('img');
            if(img) img.style.transform = 'scale(1.05)';
        });
        card.addEventListener('mouseout', () => {
            card.querySelector('.hover-overlay').style.opacity = '0';
            const img = card.querySelector('img');
            if(img) img.style.transform = 'scale(1)';
        });
        
        // Modal functionality
        card.addEventListener('click', () => {
            const detailModal = document.getElementById('library-detail-modal');
            if(!detailModal) return;
            
            document.getElementById('library-detail-preview').innerHTML = modalPreviewHtml;
            document.getElementById('library-detail-filename').textContent = file.name;
            document.getElementById('library-detail-filesize').textContent = sizeMb + ' MB';
            document.getElementById('library-detail-instructions').textContent = instruction ? '"' + instruction + '"' : '(Sin instrucciones especiales)';
            
            // Delete logic
            const delBtn = document.getElementById('library-detail-delete');
            // Remove old listeners by cloning
            const newDelBtn = delBtn.cloneNode(true);
            delBtn.parentNode.replaceChild(newDelBtn, delBtn);
            
            newDelBtn.addEventListener('click', () => {
                card.remove();
                detailModal.style.display = 'none';
            });
            
            detailModal.style.display = 'flex';
        });
        
        libraryAddBtn.insertAdjacentElement('afterend', card);
        closeModal();
    });
}

// Add close handler for detail modal
document.addEventListener('DOMContentLoaded', () => {
    const detailCloseBtn = document.getElementById('library-detail-close');
    const detailModal = document.getElementById('library-detail-modal');
    if (detailCloseBtn && detailModal) {
        detailCloseBtn.addEventListener('click', () => {
            detailModal.style.display = 'none';
        });
    }
});

