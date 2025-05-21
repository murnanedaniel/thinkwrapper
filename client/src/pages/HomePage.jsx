import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="bg-white">
      {/* Main content - extremely minimal, centered */}
      <section className="py-24 md:py-32 px-4">
        <div className="max-w-3xl mx-auto text-center space-y-8">
          <h1 className="text-3xl md:text-4xl font-normal text-gray-900">
            ThinkWrapper Newsletter Generator
          </h1>
          
          <p className="text-lg text-gray-700 max-w-xl mx-auto">
            Generate AI-written newsletters on any topic with just a few clicks
          </p>

          {/* Search-like interface inspired by EPPSU Explorer */}
          <div className="max-w-xl mx-auto mt-12 mb-16">
            <div className="border border-gray-300 rounded-md flex items-center">
              <input 
                type="text" 
                placeholder="Enter your newsletter topic..." 
                className="w-full px-4 py-3 outline-none text-gray-800"
              />
              <Link to="/create" className="px-6 py-3 border-l border-gray-300 text-gray-700 hover:text-gray-900">
                Create
              </Link>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row justify-center space-y-3 sm:space-y-0 sm:space-x-6">
            <Link 
              to="/create" 
              className="px-5 py-2 border border-gray-300 rounded text-gray-800 hover:border-gray-400"
            >
              Create Your First Newsletter
            </Link>
            <a 
              href="#how-it-works" 
              className="px-5 py-2 text-gray-600 hover:text-gray-800"
            >
              Learn More
            </a>
          </div>
        </div>
      </section>

      {/* How It Works - Extremely simplified */}
      <section id="how-it-works" className="py-16 border-t border-gray-100">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-2xl text-center text-gray-900 mb-12">
            How It Works
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="text-gray-500 mb-2">Step 1</div>
              <h3 className="text-lg text-gray-900 mb-1">
                Choose a Topic
              </h3>
              <p className="text-gray-600">
                Select any topic you're passionate about
              </p>
            </div>
            <div className="text-center">
              <div className="text-gray-500 mb-2">Step 2</div>
              <h3 className="text-lg text-gray-900 mb-1">
                Set a Schedule
              </h3>
              <p className="text-gray-600">
                Decide how often to send your newsletter
              </p>
            </div>
            <div className="text-center">
              <div className="text-gray-500 mb-2">Step 3</div>
              <h3 className="text-lg text-gray-900 mb-1">
                Hit Generate
              </h3>
              <p className="text-gray-600">
                Our AI writes engaging content for you
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing - Much simpler */}
      <section className="py-16 border-t border-gray-100">
        <div className="max-w-xl mx-auto px-4 text-center">
          <h2 className="text-2xl text-gray-900 mb-8">
            Simple Pricing
          </h2>
          <div className="text-4xl font-normal text-gray-900 mb-6">
            $9/month
          </div>
          <ul className="mb-8 space-y-2 inline-block text-left">
            <li className="flex items-center text-gray-700">
              <span className="mr-2 text-gray-400">•</span>
              Unlimited newsletters
            </li>
            <li className="flex items-center text-gray-700">
              <span className="mr-2 text-gray-400">•</span>
              Weekly generation
            </li>
            <li className="flex items-center text-gray-700">
              <span className="mr-2 text-gray-400">•</span>
              Custom topics
            </li>
            <li className="flex items-center text-gray-700">
              <span className="mr-2 text-gray-400">•</span>
              Email delivery
            </li>
          </ul>
          <Link 
            to="/create" 
            className="inline-block px-6 py-2 border border-gray-300 rounded text-gray-800 hover:border-gray-400"
          >
            Get Started
          </Link>
        </div>
      </section>
    </div>
  )
}

export default HomePage 