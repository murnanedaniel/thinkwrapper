import { Link } from 'react-router-dom'

function HomePage() {
  return (
    <div className="home-page">
      <section className="hero">
        <h1>ThinkWrapper Newsletter Generator</h1>
        <p className="lead">
          Generate AI-written newsletters on any topic with just a few clicks
        </p>
        <div className="cta-buttons">
          <Link to="/create" className="btn btn-primary">
            Create Your First Newsletter
          </Link>
          <a href="#how-it-works" className="btn btn-outline">
            Learn More
          </a>
        </div>
      </section>

      <section id="how-it-works" className="how-it-works">
        <h2>How It Works</h2>
        <div className="steps">
          <div className="step">
            <div className="step-number">1</div>
            <h3>Choose a Topic</h3>
            <p>Select any topic you're passionate about</p>
          </div>
          <div className="step">
            <div className="step-number">2</div>
            <h3>Set a Schedule</h3>
            <p>Decide how often to send your newsletter</p>
          </div>
          <div className="step">
            <div className="step-number">3</div>
            <h3>Hit Generate</h3>
            <p>Our AI writes engaging content for you</p>
          </div>
        </div>
      </section>

      <section className="pricing">
        <h2>Simple Pricing</h2>
        <div className="price-card">
          <h3>$9/month</h3>
          <ul>
            <li>Unlimited newsletters</li>
            <li>Weekly generation</li>
            <li>Custom topics</li>
            <li>Email delivery</li>
          </ul>
          <Link to="/create" className="btn btn-primary">
            Get Started
          </Link>
        </div>
      </section>
    </div>
  )
}

export default HomePage 