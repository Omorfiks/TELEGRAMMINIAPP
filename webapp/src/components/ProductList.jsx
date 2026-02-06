import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ProductList() {
  const [products, setProducts] = useState([])
  const [loading, setLoading] = useState(true)
  const navigate = useNavigate()

  useEffect(() => {
    fetchProducts()
  }, [])

  const fetchProducts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/products`)
      const data = await response.json()
      setProducts(data)
    } catch (error) {
      console.error('Error fetching products:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="text-lg">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold mb-6 text-gray-100">Каталог товаров</h1>
      <div className="grid grid-cols-2 gap-4">
        {products.map((product) => {
          const hasStock = product.sizes && Object.values(product.sizes).some(qty => qty > 0)
          
          return (
            <div
              key={product.id}
              onClick={() => navigate(`/product/${product.id}`)}
              className="bg-gray-800 rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow border border-gray-700"
            >
              {product.image_url && (
                <img
                  src={`${API_URL}${product.image_url}`}
                  alt={product.name}
                  className="w-full h-48 object-cover"
                />
              )}
              <div className="p-4">
                <h3 className="font-semibold text-sm mb-2 line-clamp-2 text-gray-100">{product.name}</h3>
                <p className="text-lg font-bold text-blue-400">{product.price} ₽</p>
                {!hasStock && (
                  <p className="text-red-400 text-xs mt-2">Нет в наличии</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
      {products.length === 0 && (
        <div className="text-center py-12">
          <p className="text-gray-400">Товары пока не добавлены</p>
        </div>
      )}
    </div>
  )
}
