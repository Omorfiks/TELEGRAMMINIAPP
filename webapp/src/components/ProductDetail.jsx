import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export default function ProductDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [product, setProduct] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchProduct()
    recordView()
  }, [id])

  const fetchProduct = async () => {
    try {
      const response = await fetch(`${API_URL}/api/products/${id}`)
      const data = await response.json()
      setProduct(data)
    } catch (error) {
      console.error('Error fetching product:', error)
    } finally {
      setLoading(false)
    }
  }

  const recordView = async () => {
    try {
      const user = window.Telegram?.WebApp?.initDataUnsafe?.user
      const user_id = user?.id || Math.floor(Math.random() * 1000000) // Fallback для тестирования
      
      await fetch(`${API_URL}/api/views`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: user_id,
          product_id: parseInt(id)
        })
      })
    } catch (error) {
      console.error('Error recording view:', error)
    }
  }

  const handleContact = () => {
    const message = `Здравствуйте! Интересует товар: ${product.name}`
    
    // Используем Telegram WebApp API если доступен
    if (window.Telegram?.WebApp?.openLink) {
      // Можно использовать openTelegramLink для открытия чата с ботом
      const botUsername = window.Telegram?.WebApp?.initDataUnsafe?.start_param || 'your_bot_username'
      const url = `https://t.me/${botUsername}?start=product_${product.id}&text=${encodeURIComponent(message)}`
      window.Telegram.WebApp.openTelegramLink(url)
    } else {
      // Fallback для тестирования вне Telegram
      const username = import.meta.env.VITE_TELEGRAM_USERNAME || 'your_telegram_username'
      const url = `https://t.me/${username}?text=${encodeURIComponent(message)}`
      window.open(url, '_blank')
    }
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-900">
        <div className="text-lg text-gray-100">Загрузка...</div>
      </div>
    )
  }

  if (!product) {
    return (
      <div className="flex justify-center items-center min-h-screen bg-gray-900">
        <div className="text-lg text-red-400">Товар не найден</div>
      </div>
    )
  }

  const sizes = product.sizes || {}
  const hasStock = Object.values(sizes).some(qty => qty > 0)
  const totalStock = Object.values(sizes).reduce((sum, qty) => sum + qty, 0)

  return (
    <div className="container mx-auto px-4 py-6 max-w-2xl">
      <button
        onClick={() => navigate('/')}
        className="mb-4 flex items-center text-blue-400 hover:text-blue-300 transition-colors"
      >
        <span className="mr-2">←</span>
        Вернуться в каталог
      </button>
      
      {product.image_url && (
        <img
          src={`${API_URL}${product.image_url}`}
          alt={product.name}
          className="w-full h-96 object-cover rounded-lg mb-6"
        />
      )}
      
      <h1 className="text-3xl font-bold mb-4 text-gray-100">{product.name}</h1>
      <p className="text-3xl font-bold text-blue-400 mb-6">{product.price} ₽</p>
      
      {product.description && (
        <div className="mb-6">
          <h2 className="text-xl font-semibold mb-2 text-gray-100">Описание</h2>
          <p className="text-gray-300">{product.description}</p>
        </div>
      )}

      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-3 text-gray-100">Размеры и остатки</h2>
        {Object.keys(sizes).length > 0 ? (
          <div className="flex flex-wrap gap-3">
            {Object.entries(sizes).map(([size, quantity]) => (
              <div
                key={size}
                className={`px-4 py-2 rounded-lg border-2 ${
                  quantity > 0
                    ? 'border-green-500 bg-green-900 text-green-200'
                    : 'border-gray-600 bg-gray-800 text-gray-400'
                }`}
              >
                <span className="font-semibold">{size}:</span> {quantity} шт.
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-400">Размеры не указаны</p>
        )}
      </div>

      {!hasStock && (
        <div className="bg-red-900 border-2 border-red-500 rounded-lg p-4 mb-6">
          <p className="text-red-200 font-semibold text-center">Нет в наличии</p>
        </div>
      )}

      {hasStock && (
        <button
          onClick={handleContact}
          className="w-full bg-blue-500 hover:bg-blue-600 text-white font-bold py-4 px-6 rounded-lg text-lg transition-colors"
        >
          💬 Написать в Telegram
        </button>
      )}
    </div>
  )
}
