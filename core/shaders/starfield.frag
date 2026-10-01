#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uStars;
uniform float uTime;
uniform vec2 uResolution;

void main() {
    vec2 uv = vTexCoord;
    
    // Twinkling stars
    float stars = texture(uStars, uv).r;
    float twinkle = sin(uTime * 0.001 * 2.0 + uv.x * 100.0 + uv.y * 100.0) * 0.5 + 0.5;
    stars *= twinkle;
    
    // Color variation - warm and cool stars
    vec3 starColor = mix(vec3(1.0, 0.95, 0.8), vec3(0.8, 0.9, 1.0), uv.y);
    
    // Subtle nebula background
    vec2 nebulaUV = uv * 2.0 + uTime * 0.00001;
    float nebula = 0.0;
    nebula += sin(nebulaUV.x * 3.0 + uTime * 0.0001) * 0.5 + 0.5;
    nebula += cos(nebulaUV.y * 2.0 - uTime * 0.00008) * 0.5 + 0.5;
    nebula = pow(nebula * 0.5, 3.0) * 0.02;
    
    vec3 color = starColor * stars * 1.5 + vec3(nebula * 0.5, nebula * 0.3, nebula * 0.1);
    
    fragColor = vec4(color, stars);
}