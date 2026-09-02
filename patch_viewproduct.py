import re

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "r") as f:
    content = f.read()

view_product_new = """  const viewProduct = async (product: Product) => {
    setSelectedProduct(product);
    setStep('product_detail');
    setUpsellData(null);
    try {
      const res = await upsellApi.getProductSuggestions(product.id);
      setUpsellData(res.data);
    } catch (err) {
      console.error('Failed to load upsell suggestions', err);
    }
  };"""
content = re.sub(r"(  const viewProduct = \(product: Product\) => \{\n    setSelectedProduct\(product\);\n    setStep\('product_detail'\);\n  \};)", view_product_new, content)

with open("frontend/src/pages/buyer/BuyerFlow.tsx", "w") as f:
    f.write(content)
