// Vanilla hash-router SPA
const routes = [
  { path: '/dashboard', component: Dashboard },
  { path: '/settings', component: Settings },
  { path: '/settings/profile', component: Profile },
];
router.push('/notifications');
window.location.hash = '#/account';
