<template>
  <div id="app" :class="{ dark: isDark }">
    <nav class="top-nav">
      <div class="nav-left">
        <span class="nav-title-blue">FinCompass</span>
        <span class="nav-title-red">PLUGIN</span>
      </div>
      <div class="nav-menu">
        <router-link to="/dashboard">Dashboard</router-link>
        <router-link to="/servers">Servers</router-link>
        <router-link to="/intentions">1. Intentions</router-link>
        <span class="arrow">→</span>
        <router-link to="/cases">2. Cases</router-link>
        <span class="arrow">→</span>
        <router-link to="/providers">3. Providers</router-link>
        <span class="arrow">→</span>
        <router-link to="/catalogs">4. Catalogs</router-link>
        <span class="arrow">→</span>
        <router-link to="/start">5. Start Magic</router-link>
        <router-link to="/pl">P&amp;L</router-link>
      </div>
      <div class="nav-right">
        <span class="icon help">?</span>
        <span class="icon sun">&#x1F31F;</span>
        <span class="user-circle">me</span>
      </div>
    </nav>
    <main>
      <router-view @gotoServers="goToServers" />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App',
  data() {
    return {
      isDark: true,
    }
  },
  methods: {
    goToServers() {
      this.$router.push('/servers');
    }
  }
}
</script>

<style>
@import url('https://fonts.googleapis.com/css?family=Montserrat:400,600,700&display=swap');

body, #app, .top-nav, .nav-title-blue, .nav-title-red, .nav-menu a, .user-circle {
  font-family: 'Montserrat', Arial, Helvetica, sans-serif;
}
.nav-title-blue {
  color: #2196f3;
  font-weight: 700;
}
.nav-title-red {
  color: #ff5252;
  font-weight: 700;
  letter-spacing: 0.1em;
}
body {
  background: #181a1b;
  color: #e0e0e0;
}
#app.dark {
  background: #181a1b;
  color: #e0e0e0;
  min-height: 100vh;
}
.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #232323;
  color: #fff;
  padding: 0.7rem 2rem 0.7rem 2rem;
  box-shadow: 0 1px 0 #333;
}
.nav-left {
  display: flex;
  align-items: center;
  font-size: 1.7rem;
  font-weight: bold;
}
.nav-menu {
  display: flex;
  gap: 2rem;
  align-items: center;
}
.nav-menu a {
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  font-size: 1rem;
  padding: 0.3rem 1rem;
  border-radius: 8px;
  transition: background 0.2s, color 0.2s;
}
.nav-menu a.router-link-active, .nav-menu a.router-link-exact-active {
  background: #4fc3f7;
  color: #232323;
}
.nav-menu a:hover {
  background: #333;
  color: #4fc3f7;
}
.nav-right {
  display: flex;
  align-items: center;
  gap: 1.2rem;
}
.icon.help {
  background: #4fc3f7;
  color: #fff;
  border-radius: 50%;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.3rem;
  font-weight: bold;
}
.icon.sun {
  font-size: 1.7rem;
  color: #ffb300;
}
.user-circle {
  background: #4fc3f7;
  color: #fff;
  border-radius: 50%;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 600;
}
main {
  max-width: 1200px;
  margin: 2rem auto;
  background: #23272a;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 16px rgba(0,0,0,0.3);
}
input {
  display: block;
  width: 100%;
  margin-bottom: 1rem;
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #444;
  background: #181a1b;
  color: #e0e0e0;
}
button {
  background: #42b983;
  color: #fff;
  border: none;
  padding: 0.7rem 1.5rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
button:hover {
  background: #369870;
}
.loading {
  text-align: center;
  font-size: 1.2rem;
  color: #aaa;
}
.server-info {
  background: #222;
  border-radius: 6px;
  padding: 1rem;
  margin-bottom: 1rem;
  color: #fff;
}
.api-key-warning {
  color: #ffb300;
  margin-top: 0.5rem;
}
.api-key-warning a {
  color: #42b983;
  margin-left: 1rem;
  text-decoration: underline;
}
.api-key-input-row {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}
.api-key-input-row input {
  flex: 1;
  padding: 0.4rem;
  border-radius: 4px;
  border: 1px solid #444;
  background: #181a1b;
  color: #e0e0e0;
}
.api-key-input-row button {
  background: #42b983;
  color: #fff;
  border: none;
  padding: 0.4rem 1rem;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: background 0.2s;
}
.api-key-input-row button:hover {
  background: #369870;
}
.nav-link.active, .nav-links a.active {
  color: #42b983;
  font-weight: bold;
  border-bottom: 2px solid #42b983;
}
</style>

<style scoped>
.arrow {
  color: #42b983;
  font-size: 0.9rem;
  font-weight: bold;
  margin: 0 -2.00rem;
}
</style>
