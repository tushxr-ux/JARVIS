#version 330 core

in vec2 vTexCoord;
out vec4 fragColor;

uniform sampler2D uTexture;
uniform vec2 uDirection; // (1,0) for horizontal, (0,1) for vertical
uniform float uWeight[5];
uniform float uRadius;

void main() {
    vec3 color = vec3(0.0);
    vec2 texOffset = uDirection * uRadius;
    
    // Center sample
    color += texture(uTexture, vTexCoord).rgb * uWeight[0];
    
    // 4 samples each side
    for (int i = 1; i < 5; i++) {
        float offset = float(i);
        color += texture(uTexture, vTexCoord + texOffset * offset).rgb * uWeight[i];
        color += texture(uTexture, vTexCoord - texOffset * offset).rgb * uWeight[i];
    }
    
    fragColor = vec4(color, 1.0);
}