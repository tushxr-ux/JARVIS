#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uTextAtlas;
uniform vec2 uTextPos;
uniform vec2 uTextSize;
uniform vec3 uColor;
uniform float uTime;
uniform float uBlink;
uniform bool uMuted;
uniform bool uSpeaking;

void main() {
    vec2 uv = vTexCoord;
    
    vec2 rel = (uv - uTextPos) / uTextSize;
    if (rel.x < 0.0 || rel.x > 1.0 || rel.y < 0.0 || rel.y > 1.0) {
        discard;
    }
    
    float text = texture(uTextAtlas, rel).r;
    
    float blinkAlpha = uBlink > 0.5 ? 1.0 : 0.3;
    
    vec3 color = uColor;
    if (uMuted) color = vec3(1.0, 0.2, 0.1);
    else if (uSpeaking) color = vec3(1.0, 0.4, 0.0);
    
    float glow = smoothstep(0.5, 0.0, abs(rel.y - 0.5) * 2.0) * 0.3;
    
    vec3 finalColor = color * text * blinkAlpha + color * glow;
    float finalAlpha = text * blinkAlpha + glow;
    
    fragColor = vec4(finalColor, finalAlpha);
}