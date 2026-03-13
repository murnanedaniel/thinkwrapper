import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="home-page">
      <section className="hero" style={{ textAlign: 'center', padding: '4rem 2rem' }}>
        <h1>ThinkWrapper Newsletter Generator</h1>
        <p className="lead" style={{ fontSize: '1.2rem', color: '#666', margin: '1rem 0 2rem' }}>
          AI-generated newsletters on any topic. Preview free, subscribe for $1/month.
        </p>
        <div className="cta-buttons">
          <Link to="/create" className="btn btn-primary">
            Try It Free
          </Link>
          <a href="#how-it-works" className="btn btn-outline">
            Learn More
          </a>
        </div>
      </section>

      <section id="how-it-works" className="how-it-works" style={{ padding: '3rem 2rem', maxWidth: '800px', margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '2rem' }}>How It Works</h2>
        <div className="steps" style={{ display: 'flex', gap: '2rem', justifyContent: 'center', flexWrap: 'wrap' }}>
          <div className="step" style={{ flex: '1', minWidth: '200px', textAlign: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#3498db', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontWeight: 'bold' }}>1</div>
            <h3>Choose a Topic</h3>
            <p>Describe what you want your newsletter about</p>
          </div>
          <div className="step" style={{ flex: '1', minWidth: '200px', textAlign: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#3498db', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontWeight: 'bold' }}>2</div>
            <h3>Preview for Free</h3>
            <p>See a real AI-generated issue before you pay</p>
          </div>
          <div className="step" style={{ flex: '1', minWidth: '200px', textAlign: 'center' }}>
            <div style={{ width: '40px', height: '40px', borderRadius: '50%', background: '#3498db', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 1rem', fontWeight: 'bold' }}>3</div>
            <h3>Subscribe</h3>
            <p>$1/month. Fresh issues delivered to your inbox.</p>
          </div>
        </div>
      </section>

      <section className="pricing" style={{ textAlign: 'center', padding: '3rem 2rem', background: 'white', margin: '2rem 0' }}>
        <h2 style={{ marginBottom: '2rem' }}>Simple Pricing</h2>
        <div style={{ maxWidth: '350px', margin: '0 auto', padding: '2rem', border: '2px solid #3498db', borderRadius: '12px' }}>
          <h3 style={{ fontSize: '2.5rem', color: '#3498db', margin: '0' }}>$1<span style={{ fontSize: '1rem', color: '#666' }}>/month</span></h3>
          <ul style={{ textAlign: 'left', margin: '1.5rem 0', listStyle: 'none', padding: 0 }}>
            <li style={{ padding: '0.5rem 0' }}>Unlimited newsletters</li>
            <li style={{ padding: '0.5rem 0' }}>AI-powered content with real sources</li>
            <li style={{ padding: '0.5rem 0' }}>Daily, weekly, or monthly delivery</li>
            <li style={{ padding: '0.5rem 0' }}>Preview before you pay</li>
          </ul>
          <Link to="/create" className="btn btn-primary" style={{ width: '100%', display: 'block' }}>
            Try It Free
          </Link>
        </div>
      </section>
    </div>
  )
}

export default HomePage
