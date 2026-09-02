import re

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "r") as f:
    content = f.read()

# Add imports
imports = """
import { campaignsApi } from '../../api/campaigns';
import { upsellApi } from '../../api/upsell';
import type { Campaign, UpsellResponse } from '../../types';
"""
content = re.sub(r"(import \{ buyerApiClient \} from '../../api/client';)", r"\1\n" + imports, content)

# Add states
states = """  const [activeCampaigns, setActiveCampaigns] = useState<Campaign[]>([]);
  const [upsellData, setUpsellData] = useState<UpsellResponse | null>(null);"""
content = re.sub(r"(  const \[authData, setAuthData\] = useState\(\{ email: '', password: '' \}\);)", r"\1\n" + states, content)

# Add fetchCampaigns function
fetch_camps = """  const fetchCampaigns = async () => {
    try {
      const res = await campaignsApi.listCampaigns();
      setActiveCampaigns(res.data.filter(c => c.status === 'ACTIVE'));
    } catch (err) {
      console.error('Failed to load campaigns', err);
    }
  };"""
content = re.sub(r"(  const fetchProducts = async \(\) => \{)", fetch_camps + r"\n\n\1", content)

# Add fetchCampaigns call in handleAuth and useEffect
content = content.replace("fetchProducts();", "fetchProducts();\n      fetchCampaigns();")

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "w") as f:
    f.write(content)
