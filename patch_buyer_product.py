import re

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "r") as f:
    content = f.read()

upsell_ui = """
          {/* Upsell / Cross-sell Suggestions */}
          {upsellData && (upsellData.upsell.length > 0 || upsellData.cross_sell.length > 0) && (
            <div className="mt-12 space-y-12 border-t pt-10">
              
              {upsellData.upsell.length > 0 && (
                <div>
                  <h3 className="text-2xl font-bold mb-6">You might also consider</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {upsellData.upsell.map(item => (
                      <Card key={item.product_id} className="cursor-pointer hover:shadow-md transition-shadow border-blue-100" onClick={() => {
                        const p = products.find(x => x.id === item.product_id);
                        if (p) viewProduct(p);
                      }}>
                        <CardContent className="p-4">
                          <div className="bg-gray-100 h-32 rounded mb-4 flex items-center justify-center">
                            <ShoppingBag className="h-10 w-10 text-gray-400" />
                          </div>
                          <div className="text-xs text-[var(--rzp-primary)] font-bold mb-1 uppercase tracking-wider">{item.category}</div>
                          <h4 className="font-bold mb-1 line-clamp-1">{item.name}</h4>
                          <p className="text-lg font-bold mb-2">{formatPrice(item.price)}</p>
                          {item.explanation && (
                            <p className="text-sm text-gray-500 line-clamp-2 italic bg-blue-50 p-2 rounded">{item.explanation}</p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

              {upsellData.cross_sell.length > 0 && (
                <div>
                  <h3 className="text-2xl font-bold mb-6">Complete your setup</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {upsellData.cross_sell.map(item => (
                      <Card key={item.product_id} className="cursor-pointer hover:shadow-md transition-shadow border-green-100" onClick={() => {
                        const p = products.find(x => x.id === item.product_id);
                        if (p) viewProduct(p);
                      }}>
                        <CardContent className="p-4">
                          <div className="bg-gray-100 h-32 rounded mb-4 flex items-center justify-center">
                            <ShoppingBag className="h-10 w-10 text-gray-400" />
                          </div>
                          <div className="text-xs text-[var(--rzp-success)] font-bold mb-1 uppercase tracking-wider">{item.category}</div>
                          <h4 className="font-bold mb-1 line-clamp-1">{item.name}</h4>
                          <p className="text-lg font-bold mb-2">{formatPrice(item.price)}</p>
                          {item.explanation && (
                            <p className="text-sm text-gray-500 line-clamp-2 italic bg-green-50 p-2 rounded">{item.explanation}</p>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}
"""

target = """                <Button onClick={addToCart} isLoading={loading} size="lg" className="px-8">
                  Add to Cart
                </Button>
              </div>
            </div>
          </div>
"""
replacement = target + upsell_ui

content = content.replace(target, replacement)

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "w") as f:
    f.write(content)
