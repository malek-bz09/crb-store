// Product categories. Products themselves now live in the backend database
// (manage them in Admin → Products) and are loaded by ProductsProvider.
// The ids must match CATEGORIES in backend/app/models/product.py; the names and
// photos are only shown in the shop.
export const categories = [
  { id: 'tops', name: 'Jerseys & Tops', image: '/crb-supporters-tee.jpg' },
  { id: 'bottoms', name: 'Shorts & Training', image: '/crb-training-joggers.jpg' },
  { id: 'hats', name: 'Caps & Hats', image: '/crb-red-knit-beanie.jpg' },
]

export const getCategoryName = (id) => categories.find((c) => c.id === id)?.name ?? id
