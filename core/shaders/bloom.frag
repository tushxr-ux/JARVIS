#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uScene;
uniform sampler2D uBloom;
uniform float uExposure;
uniform float uGamma;
uniform bool uMuted;

void main() {
    vec3 scene = texture(uScene, vTexCoord).rgb;
    vec3 bloom = texture(uBloom, vTexCoord).rgb;
    
    // Tone mapping
    vec3 color = scene + bloom * 0.8;
    color = vec3(1.0) - exp(-color * uExposure);
    
    // Gamma correction
    color = pow(color, vec3(1.0 / uGamma));
    
    // Muted tint
    if (uMuted) {
        color = mix(color, vec3(0.3, 0.05, 0.02), 0.4);
    }
    
    // Subtle vignette
    float vignette = 1.0 - length(vTexCoord - 0.5) * 0.6;
    color *= vignette;
    
    // Scanline effect (subtle)
    float scanline = 1.0 - 0.02 * sin(vTexCoord.y * 800.0);
    color *= scanline;
    
    fragColor = vec4(color, 1.0);
}