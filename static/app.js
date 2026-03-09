const state = {
    token: localStorage.getItem("token") || null,
    currentUser: null
};

// 1. СИСТЕМА СПОВІЩЕНЬ (Toast)
function showToast(message, type = "success") {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.style.backgroundColor = type === "success" ? "var(--success)" : "var(--danger)";
    toast.innerText = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = '0.5s';
        setTimeout(() => toast.remove(), 500);
    }, 3000);
}

function navigate(pageId) {
    document.querySelectorAll('.page').forEach(page => page.classList.remove('active'));
    document.getElementById(`page-${pageId}`).classList.add('active');
    document.getElementById('global-error').style.display = 'none';

    if (pageId === 'home') loadPosts();
    if (pageId === 'profile') loadMyProfile();
}

function updateUI() {
    const isLogged = !!state.token;
    document.getElementById('nav-login').style.display = isLogged ? 'none' : 'inline-block';
    document.getElementById('nav-profile').style.display = isLogged ? 'inline-block' : 'none';
    document.getElementById('nav-logout').style.display = isLogged ? 'inline-block' : 'none';
}

// АВТОРИЗАЦІЯ
async function login() {
    const formData = new URLSearchParams();
    formData.append('username', document.getElementById('login-username').value);
    formData.append('password', document.getElementById('login-password').value);

    try {
        const r = await fetch('/login', { method: 'POST', body: formData });
        if (!r.ok) throw new Error("Неправильний логін або пароль");
        const data = await r.json();
        state.token = data.access_token;
        localStorage.setItem("token", state.token);
        updateUI();
        showToast("Ви успішно увійшли!");
        navigate('home');
    } catch (e) { showToast(e.message, "error"); }
}

async function register() {
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;

    try {
        const r = await fetch('/users/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        if (!r.ok) {
            const err = await r.json();
            throw new Error(err.detail || "Помилка реєстрації");
        }
        showToast("Реєстрація успішна! Тепер увійдіть.");
    } catch (e) { showToast(e.message, "error"); }
}

function logout() {
    state.token = null;
    localStorage.removeItem("token");
    updateUI();
    showToast("Ви вийшли з акаунта");
    navigate('home');
}

// РОБОТА З ПОСТАМИ
async function loadPosts() {
    const sortBy = document.getElementById('sort-select').value;
    const search = document.getElementById('search-input').value;

    try {
        const url = `/posts/?sort_by=${sortBy}${search ? `&search=${search}` : ''}`;
        const response = await fetch(url);
        const posts = await response.json();
        const container = document.getElementById('posts-container');

        container.innerHTML = posts.length ? posts.map(post => `
            <div class="post">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h3>${post.title}</h3>
                    <small style="color: var(--text-muted)">${new Date(post.created_at).toLocaleString()}</small>
                </div>
                <p>${post.content}</p>
                <div style="background: #f9fafb; padding: 10px; border-radius: 8px; margin-top: 15px;">
                    <strong style="font-size: 14px;">Коментарі:</strong>
                    ${post.comments.map(c => `<div style="font-size: 13px; border-bottom: 1px solid #eee; padding: 5px 0;">${c.text}</div>`).join('') || '<div style="font-size: 13px; color: var(--text-muted);">Немає коментарів</div>'}
                    ${state.token ? `
                        <div style="display: flex; gap: 5px; margin-top: 10px;">
                            <input type="text" id="com-input-${post.id}" placeholder="Ваш коментар..." style="margin-bottom: 0; padding: 8px;">
                            <button class="secondary-btn" onclick="addComment(${post.id})" style="padding: 5px 12px; font-size: 13px;">OK</button>
                        </div>
                    ` : ''}
                </div>
            </div>
        `).join('') : '<p>Постів не знайдено</p>';
    } catch (e) { showToast("Помилка завантаження", "error"); }
}

async function loadMyProfile() {
    if (!state.token) return navigate('login');
    try {
        const userRes = await fetch('/users/me/', { headers: { 'Authorization': `Bearer ${state.token}` } });
        state.currentUser = await userRes.json();
        document.getElementById('profile-username').innerText = state.currentUser.username;

        const postsRes = await fetch('/users/me/posts/', { headers: { 'Authorization': `Bearer ${state.token}` } });
        const myPosts = await postsRes.json();

        document.getElementById('my-posts-list').innerHTML = myPosts.map(p => `
            <div class="post" style="padding: 15px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong style="font-size: 14px;">${p.title}</strong>
                    <div style="display: flex; gap: 5px;">
                        <button onclick="openEdit(${p.id}, '${p.title.replace(/'/g, "\\'")}', '${p.content.replace(/'/g, "\\'")}')" class="secondary-btn" style="font-size: 12px;">Редагувати</button>
                        <button onclick="deletePost(${p.id})" style="background: #fee2e2; color: #dc2626; border: none; padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 12px;">Видалити</button>
                    </div>
                </div>
            </div>
        `).join('') || '<p>У вас ще немає публікацій</p>';
    } catch (e) { logout(); }
}

// КЕРУВАННЯ (PUT, DELETE, POST)
async function createPost() {
    const title = document.getElementById('new-post-title').value;
    const content = document.getElementById('new-post-content').value;
    if (!title || !content) return showToast("Заповніть всі поля", "error");

    try {
        const r = await fetch('/posts/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({ title, content })
        });
        if (!r.ok) throw new Error("Помилка створення");
        showToast("Пост опубліковано!");
        document.getElementById('new-post-title').value = '';
        document.getElementById('new-post-content').value = '';
        navigate('home');
    } catch (e) { showToast(e.message, "error"); }
}

async function deletePost(id) {
    if (!confirm("Видалити цей пост?")) return;
    try {
        const r = await fetch(`/posts/${id}`, { method: 'DELETE', headers: { 'Authorization': `Bearer ${state.token}` } });
        if (!r.ok) throw new Error("Не вдалося видалити");
        showToast("Пост видалено");
        loadMyProfile();
    } catch (e) { showToast(e.message, "error"); }
}

// РЕДАГУВАННЯ
function openEdit(id, title, content) {
    document.getElementById('edit-post-id').value = id;
    document.getElementById('edit-post-title').value = title;
    document.getElementById('edit-post-content').value = content;
    document.getElementById('edit-modal').style.display = 'block';
}

function closeEdit() { document.getElementById('edit-modal').style.display = 'none'; }

async function saveEdit() {
    const id = document.getElementById('edit-post-id').value;
    const data = {
        title: document.getElementById('edit-post-title').value,
        content: document.getElementById('edit-post-content').value
    };
    try {
        const r = await fetch(`/posts/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify(data)
        });
        if (!r.ok) throw new Error("Помилка оновлення");
        showToast("Пост успішно оновлено!");
        closeEdit();
        loadMyProfile();
    } catch (e) { showToast(e.message, "error"); }
}

async function addComment(postId) {
    const text = document.getElementById(`com-input-${postId}`).value;
    if (!text) return;
    try {
        await fetch('/comments/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${state.token}` },
            body: JSON.stringify({ text, post_id: postId })
        });
        document.getElementById(`com-input-${postId}`).value = '';
        loadPosts();
        showToast("Коментар додано");
    } catch (e) { showToast("Помилка коментаря", "error"); }
}

updateUI();
loadPosts();