/**
 * IBCo JavaScript Client Example
 *
 * Demonstrates how to use the IBCo API with JavaScript's fetch API.
 * Can be used in Node.js or browser environments.
 *
 * Usage (Node.js):
 *   node fetch_risk_scores.js
 *
 * Usage (Browser):
 *   <script src="fetch_risk_scores.js"></script>
 *   <script>
 *     const client = new IBCoClient();
 *     client.getCurrentRiskScore(1).then(data => console.log(data));
 *   </script>
 */

class IBCoClient {
  constructor(baseUrl = 'https://api.ibco-ca.us/api/v1', apiToken = null) {
    this.baseUrl = baseUrl;
    this.apiToken = apiToken;
  }

  /**
   * Make API request with proper headers and error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;

    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (this.apiToken) {
      headers['Authorization'] = `Bearer ${this.apiToken}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      // Handle rate limiting
      if (response.status === 429) {
        const retryAfter = response.headers.get('Retry-After') || 60;
        throw new Error(`Rate limit exceeded. Retry after ${retryAfter} seconds.`);
      }

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.message || `HTTP ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${error.message}`);
      throw error;
    }
  }

  /**
   * Get list of cities
   */
  async getCities(state = null) {
    const params = new URLSearchParams();
    if (state) params.append('state', state);

    const endpoint = `/cities${params.toString() ? '?' + params.toString() : ''}`;
    const data = await this.request(endpoint);

    return data.cities;
  }

  /**
   * Get current risk score for a city
   */
  async getCurrentRiskScore(cityId) {
    return await this.request(`/risk/cities/${cityId}/current`);
  }

  /**
   * Get risk score history
   */
  async getRiskHistory(cityId, startYear = null, endYear = null) {
    const params = new URLSearchParams();
    if (startYear) params.append('start_year', startYear);
    if (endYear) params.append('end_year', endYear);

    const endpoint = `/risk/cities/${cityId}/history${params.toString() ? '?' + params.toString() : ''}`;
    return await this.request(endpoint);
  }

  /**
   * Get fiscal cliff analysis
   */
  async getFiscalCliff(cityId, scenario = 'base') {
    const params = new URLSearchParams({ scenario });
    return await this.request(`/projections/cities/${cityId}/fiscal-cliff?${params.toString()}`);
  }

  /**
   * Get pension status
   */
  async getPensionStatus(cityId, fiscalYear) {
    const params = new URLSearchParams({ fiscal_year: fiscalYear });
    return await this.request(`/pensions/cities/${cityId}/status?${params.toString()}`);
  }
}

/**
 * Example usage
 */
async function main() {
  const client = new IBCoClient();
  const cityId = 1; // Vallejo

  console.log('='.repeat(60));
  console.log('IBCo API JavaScript Client Example');
  console.log('='.repeat(60));

  try {
    // 1. Get cities
    console.log('\n1. Getting cities...');
    const cities = await client.getCities('CA');
    console.log(`Found ${cities.length} cities in California:`);
    cities.slice(0, 5).forEach(city => {
      console.log(`  - ${city.name} (ID: ${city.id})`);
    });

    // 2. Get current risk score
    console.log(`\n2. Getting current risk score for city ${cityId}...`);
    const riskScore = await client.getCurrentRiskScore(cityId);
    console.log(`City: ${riskScore.city_name}`);
    console.log(`Fiscal Year: ${riskScore.fiscal_year}`);
    console.log(`Overall Score: ${riskScore.overall_score}/100 (${riskScore.risk_level})`);
    console.log('Category Scores:');
    Object.entries(riskScore.category_scores).forEach(([category, score]) => {
      console.log(`  - ${category}: ${score}/100`);
    });

    // 3. Get risk history
    console.log('\n3. Getting risk score history...');
    const history = await client.getRiskHistory(cityId, 2020);
    console.log(`Trend: ${history.trend}`);
    console.log('Historical Scores:');
    history.risk_scores.forEach(item => {
      console.log(`  - FY${item.fiscal_year}: ${item.overall_score}/100`);
    });

    // 4. Get fiscal cliff
    console.log('\n4. Getting fiscal cliff analysis...');
    const cliff = await client.getFiscalCliff(cityId, 'base');
    if (cliff.has_fiscal_cliff) {
      console.log('⚠ Fiscal Cliff Warning:');
      console.log(`  Cliff Year: FY${cliff.fiscal_cliff_year}`);
      console.log(`  Years Until Cliff: ${cliff.years_until_cliff}`);
      console.log(`  Revenue Increase Needed: ${cliff.revenue_increase_needed_percent.toFixed(1)}%`);
    } else {
      console.log('✓ No fiscal cliff projected');
    }

    // 5. Get pension status
    console.log('\n5. Getting pension status...');
    const pensions = await client.getPensionStatus(cityId, 2024);
    console.log(`Average Funded Ratio: ${(pensions.avg_funded_ratio * 100).toFixed(1)}%`);
    console.log(`Total UAL: $${pensions.total_ual.toLocaleString()}`);
    console.log('Plans:');
    pensions.plans.forEach(plan => {
      console.log(`  - ${plan.plan_name}: ${(plan.funded_ratio * 100).toFixed(1)}% funded`);
    });

    console.log('\n' + '='.repeat(60));
    console.log('✓ Examples completed successfully!');
    console.log('='.repeat(60));

  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exit(1);
  }
}

// Run if executed directly (Node.js)
if (typeof require !== 'undefined' && require.main === module) {
  main();
}

// Export for use as module
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { IBCoClient };
}
