// React/Vue style route table, history mode
const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/users', component: Users },
    { path: '/users/:id', component: UserDetail },
    { path: '/reports/weekly', component: WeeklyReport },
  ],
});
router.push('/onboarding');
const menu = `<Link to="/pricing">Pricing</Link><Route path="/billing" />`;
