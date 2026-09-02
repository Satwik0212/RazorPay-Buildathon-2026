import re

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "r") as f:
    content = f.read()

campaign_banner = """          {activeCampaigns.length > 0 && (
            <div className="mb-8 space-y-4">
              {activeCampaigns.map(camp => (
                <div key={camp.id} className="bg-gradient-to-r from-[var(--rzp-primary-soft)] to-blue-50 border border-[var(--rzp-primary)] rounded-lg p-6 shadow-sm flex items-center justify-between">
                  <div>
                    <span className="bg-blue-100 text-[var(--rzp-primary)] text-xs font-bold px-2 py-1 rounded uppercase tracking-wider mb-2 inline-block">
                      Special Offer
                    </span>
                    <h3 className="text-xl font-bold text-gray-900">{camp.name}</h3>
                    <p className="text-gray-700 mt-1">{camp.message_content}</p>
                  </div>
                  {camp.target_product_id && (
                    <Button onClick={() => {
                      const p = products.find(x => x.id === camp.target_product_id);
                      if (p) viewProduct(p);
                    }}>
                      View Offer
                    </Button>
                  )}
                </div>
              ))}
            </div>
          )}
"""
content = content.replace("{renderHeader('Discover Products')}", "{renderHeader('Discover Products')}\n" + campaign_banner)

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "w") as f:
    f.write(content)
