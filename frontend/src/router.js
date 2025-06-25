import { createRouter, createWebHashHistory } from 'vue-router'
import FinCompassDashboard from './components/Dashboard.vue'
import FinCompassServers from './components/Servers.vue'
import FinCompassProviders from './components/Providers.vue'
import FinCompassPL from './components/PL.vue'
import FinCompassIntentions from './components/Intentions.vue'
import FinCompassCatalogs from './components/Catalogs.vue'
import FinCompassCases from './components/Cases.vue'
import StartMagic from './components/Start.vue'

const routes = [
  { path: '/', redirect: '/dashboard' },
  { path: '/dashboard', component: FinCompassDashboard },
  { path: '/start', component: StartMagic },
  { path: '/servers', component: FinCompassServers },
  { path: '/providers', component: FinCompassProviders },
  { path: '/catalogs', component: FinCompassCatalogs },
  { path: '/cases', component: FinCompassCases },
  { path: '/intentions', component: FinCompassIntentions },
  { path: '/pl', component: FinCompassPL },
  // ...add other routes here...
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

export default router 