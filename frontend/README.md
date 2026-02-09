# 🍫 Le Sommelier - AI Chocolate Recommendation System

An intelligent chocolate sommelier powered by Next.js and OpenAI, featuring a comprehensive database of 2000+ fine chocolates.

## ✨ Features

- **AI-Powered Conversations**: Interactive chat with OpenAI GPT-4 integration
- **Comprehensive Database**: 2000+ chocolates with detailed tasting notes and origins
- **Intelligent Filtering**: Geographic, flavor profile, cocoa percentage, and budget filtering
- **Premium Design**: Dark theme with gold accents and glassmorphism effects
- **Responsive Interface**: Optimized for desktop and mobile devices
- **Professional Branding**: Custom logo integration and sophisticated typography

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- OpenAI API key (optional, fallback system included)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/plakoplister/chocolate-sommelier-ai.git
cd chocolate-sommelier-ai/SOMMELIER
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.local.example .env.local
# Add your OpenAI API key (optional)
OPENAI_API_KEY=your_api_key_here
```

4. Start the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser

## 🎯 How It Works

### 1. **Intelligent Conversation Flow**
- Progressive questioning requiring 5 preference categories
- Cocoa percentage preferences (50-60% mild, 70-75% balanced, 80%+ intense)
- Flavor profiles (fruity, spicy, floral, earthy, nutty, caramel)
- Geographic origins (South America, Africa, Asia, specific countries)
- Budget considerations (economical, standard, premium)
- Occasion context (gift, tasting, cooking, special events)

### 2. **Advanced Recommendation Engine**
- Multi-criteria scoring algorithm
- Geographic filtering with continent mapping
- Fallback suggestions when no matches found
- Detailed chocolate information with context

### 3. **Premium User Experience**
- Fixed chat input with responsive design
- Elegant message bubbles with avatars
- Smooth animations and hover effects
- Professional logo and branding integration

## 🛠️ Technical Stack

- **Frontend**: Next.js 14, React 18, JavaScript
- **AI Integration**: OpenAI GPT-4 API
- **Data Processing**: Excel to JSON conversion
- **Styling**: Custom CSS with CSS variables
- **Typography**: Playfair Display & Montserrat fonts
- **Architecture**: Modular component structure

## 📊 Database

The system includes a comprehensive chocolate database with:
- **2000+ chocolates** from premium manufacturers
- **Detailed tasting notes** and flavor profiles
- **Geographic origins** with precise country mapping
- **Cocoa percentages** and pricing information
- **Professional reviews** and ratings

## 🎨 Design System

- **Color Palette**: Dark theme with gold accents (#D4AF37)
- **Typography Scale**: Hierarchical font sizing with CSS custom properties
- **Component Library**: Reusable UI components with consistent styling
- **Responsive Design**: Mobile-first approach with breakpoint optimization
- **Animations**: Smooth transitions and micro-interactions

## 🔧 Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your_openai_api_key  # Optional
```

### Customization

- **Logo**: Replace `/public/logo-Sommelier.png` with your logo
- **Colors**: Modify CSS custom properties in `/src/styles/globals.css`
- **Database**: Update `/data/chocolates.json` with additional chocolates
- **Conversation Flow**: Customize prompts in `/src/services/openai-sommelier.js`

## 📁 Project Structure

```
SOMMELIER/
├── src/
│   ├── components/
│   │   ├── Chat/          # Chat interface components
│   │   ├── Recommendations/ # Chocolate recommendation cards
│   │   └── UI/            # Reusable UI components
│   ├── pages/             # Next.js pages and API routes
│   ├── services/          # AI and recommendation logic
│   └── styles/            # Global styles and CSS variables
├── data/                  # Chocolate database files
├── public/                # Static assets (logo, images)
└── package.json          # Dependencies and scripts
```

## 🚀 Deployment

### Vercel (Recommended)

1. Push to GitHub
2. Connect to Vercel
3. Add environment variables
4. Deploy automatically

### Other Platforms

Compatible with:
- Netlify
- Railway
- Heroku
- AWS Amplify

## 🤝 Contributing

Contributions are welcome! Please feel free to:

- Add new chocolates to the database
- Improve the recommendation algorithm
- Enhance the user interface
- Add new features and functionality

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- OpenAI for GPT-4 integration
- Next.js team for the excellent framework
- Chocolate industry data sources
- Design inspiration from premium chocolate brands

---

*Built with ❤️ for chocolate enthusiasts worldwide*