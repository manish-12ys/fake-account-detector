const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

class ClassList {
    constructor() { this.values = new Set(); }
    add(...names) { names.forEach((name) => this.values.add(name)); }
    remove(...names) { names.forEach((name) => this.values.delete(name)); }
    contains(name) { return this.values.has(name); }
}

class Node {
    constructor(tagName = '#text') {
        this.tagName = tagName;
        this.children = [];
        this.textContent = '';
        this.value = '';
        this.innerHTML = '';
        this.classList = new ClassList();
        this.className = '';
    }
    appendChild(child) { this.children.push(child); return child; }
    addEventListener() {}
    scrollIntoView() {}
    get renderedText() { return this.textContent + this.children.map((child) => child.renderedText).join(''); }
}

const ids = ['analysis-form', 'fetch-btn', 'username', 'fetch-error', 'error-message',
    'skip-section', 'loading', 'bio', 'followers', 'following', 'posts', 'profile-pic',
    'fetched-profile', 'profile-data'];
const elements = Object.fromEntries(ids.map((id) => [id, new Node(id)]));
elements['fetched-profile'].classList.add('hidden');
elements['fetch-error'].classList.add('hidden');
elements['skip-section'].classList.add('hidden');
elements.loading.classList.add('hidden');

const document = {
    getElementById(id) { return elements[id]; },
    createElement(tagName) { return new Node(tagName); },
    createTextNode(text) { const node = new Node(); node.textContent = String(text); return node; },
};

const context = {
    document,
    setTimeout(callback) { callback(); },
    fetch: async () => ({ ok: true, json: async () => ({ success: true, profile: {} }) }),
};
vm.runInNewContext(fs.readFileSync('static/app.js', 'utf8') + '\nthis.fetchInstagram = fetchInstagram;', context);

async function fetchProfile(profileResponse) {
    context.fetch = async () => ({ ok: true, json: async () => profileResponse });
    elements.username.value = 'safe_user';
    await context.fetchInstagram();
}

(async () => {
    await fetchProfile({
        success: true,
        profile: {
            username: '<img src=x onerror=alert(1)>',
            bio: '✨ line one\nline two',
            followers_count: 111,
            following_count: 222,
            media_count: 3,
            profile_pic_url: null,
            warnings: ['Profile data may be incomplete'],
        },
    });

    assert.equal(elements.bio.value, '✨ line one\nline two');
    assert.equal(elements.following.value, 222);
    assert.equal(elements['fetched-profile'].classList.contains('hidden'), false);
    assert.match(elements['profile-data'].renderedText, /@<img src=x onerror=alert\(1\)>/);
    assert.equal(elements['profile-data'].innerHTML, '', 'profile content must not use innerHTML');
    assert.match(elements['profile-data'].renderedText, /Profile data may be incomplete/);

    context.fetch = async () => { throw new Error('offline'); };
    await context.fetchInstagram();
    assert.equal(elements['fetched-profile'].classList.contains('hidden'), true);
    assert.match(elements['error-message'].textContent, /Network error/);
    console.log('profile UI tests passed');
})().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});
