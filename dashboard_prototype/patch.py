import base64

with open('logo_elcano.png', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()

with open('index.html', 'r', encoding='utf-8') as f:
    html = f.read()

logo_data = f'data:image/png;base64,{b64}'

# 1. Fix logo: remove white invert filter, keep it natural
html = html.replace(
    '.nav-logo img {\n            height: 48px;\n            filter: brightness(0) invert(1);\n        }',
    '.nav-logo img {\n            height: 48px;\n        }'
)
# Also fix footer logo filter
html = html.replace(
    'filter: brightness(0) invert(0.5);',
    ''
)

# 2. Add rotating globe in hero section
# Replace the scroll indicator section to add globe before it
globe_html = '''
    <div id="heroGlobe" style="width: 480px; height: 480px; margin: -2rem auto 0; position: relative; z-index: 1;"></div>
'''

html = html.replace(
    '    <div class="scroll-indicator">',
    globe_html + '\n    <div class="scroll-indicator">'
)

# 3. Add globe initialization JS before the closing </script>
globe_js = '''

// ============================================
// HERO ROTATING GLOBE
// ============================================
function initGlobe() {
    const profiles = DATA.profiles;
    
    const globeData = [{
        type: 'choropleth',
        locationmode: 'ISO-3',
        locations: profiles.map(p => p.country),
        z: profiles.map(p => p.vulnerability),
        text: profiles.map(p => getName(p.country)),
        hoverinfo: 'text+z',
        colorscale: [
            [0, '#1a1f2e'],
            [0.3, '#3d1515'],
            [0.5, '#6b1f1f'],
            [0.7, '#8b2525'],
            [0.9, '#bb2521'],
            [1, '#ff4040']
        ],
        showscale: false,
        marker: { line: { color: '#0a0e17', width: 0.3 } }
    }];

    let rotation = { lon: -20, lat: 15 };

    const layout = {
        geo: {
            projection: { type: 'orthographic', rotation: rotation },
            bgcolor: 'rgba(0,0,0,0)',
            showframe: false,
            showcoastlines: true,
            coastlinecolor: '#2a3040',
            showland: true,
            landcolor: '#1a2332',
            showocean: true,
            oceancolor: '#0d1117',
            showlakes: false,
            showcountries: true,
            countrycolor: '#1e2838',
            lonaxis: { showgrid: false },
            lataxis: { showgrid: false }
        },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        margin: { t: 0, b: 0, l: 0, r: 0 },
        font: { family: 'Inter' }
    };

    Plotly.newPlot('heroGlobe', globeData, layout, {
        responsive: true,
        displayModeBar: false,
        scrollZoom: false
    });

    // Animate rotation
    let animating = true;
    function rotate() {
        if (!animating) return;
        rotation.lon += 0.3;
        Plotly.relayout('heroGlobe', {
            'geo.projection.rotation.lon': rotation.lon
        });
        requestAnimationFrame(rotate);
    }
    rotate();

    // Pause on hover
    const globeEl = document.getElementById('heroGlobe');
    globeEl.addEventListener('mouseenter', () => { animating = false; });
    globeEl.addEventListener('mouseleave', () => { animating = true; rotate(); });
    
    // Click on globe country
    globeEl.on('plotly_click', function(data) {
        if (data.points[0]) {
            showProfile(data.points[0].location);
        }
    });
}
'''

html = html.replace(
    "// ============================================\n// NAV SCROLL EFFECT",
    globe_js + "\n// ============================================\n// NAV SCROLL EFFECT"
)

# Add initGlobe() call
html = html.replace(
    '        initSearch();',
    '        initSearch();\n        initGlobe();'
)

with open('index.html', 'w', encoding='utf-8') as f:
    f.write(html)

print('Done - logo fixed, rotating globe added')
