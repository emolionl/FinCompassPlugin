<template>
  <div class="pl-view">
    <h2>P&amp;L</h2>
    <div class="external-link-container">
      <p>For detailed Profit & Loss analysis, please visit our main platform.</p>
      <a :href="externalUrl" target="_blank" rel="noopener" class="external-link-button">
        Go to External P&L
      </a>
    </div>
  </div>
</template>

<script>
export default {
  name: 'FinCompassPL',
  data() {
    return {
      // Replace with your actual external P&L URL
      externalUrl: 'https://fincompass.emolio.nl/app/#/pnl'
    }
  }
}
</script>

<style scoped>
.pl-view {
  text-align: center;
  padding: 2rem;
  color: #e0e0e0;
}
.external-link-container {
  margin: 4rem auto;
  padding: 2rem;
  background: #333;
  border-radius: 8px;
  max-width: 500px;
}
.external-link-button {
  display: inline-block;
  background: #4fc3f7;
  color: #232323;
  text-decoration: none;
  font-weight: 600;
  font-size: 1.1rem;
  padding: 0.8rem 1.5rem;
  border-radius: 8px;
  transition: background 0.2s;
  margin-top: 1rem;
}
.external-link-button:hover {
  background: #2196f3;
}
</style> 