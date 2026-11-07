// Product categories. Products themselves now live in the backend database
// (manage them in Admin → Products) and are loaded by ProductsProvider.
// The ids must match CATEGORIES in app/api/app/models/product.py; the names and
// photos are only shown in the shop.
export const categories = [
  { id: 'tops', name: 'Jerseys & Tops', image: '/crb-home-jersey.jpg' },
  { id: 'bottoms', name: 'Shorts & Training', image: '/crb-tracksuit.webp' },
  { id: 'hats', name: 'Caps & Hats', image: '/supporters-merch.jpg' },
]

export const getCategoryName = (id) => categories.find((c) => c.id === id)?.name ?? id
