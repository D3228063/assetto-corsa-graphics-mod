#version 300 es
precision highp float;

in vec2 vTexCoord;
layout(location = 0) out vec4 fragColor;

uniform sampler2D uSceneTexture;
uniform sampler2D uBloomTexture;
uniform sampler2D uVelocityTexture;
uniform vec2 uResolution;
uniform float uExposure;
uniform float uContrast;
uniform float uSaturation;
uniform float uBloomStrength;
uniform float uMotionBlurStrength;
uniform float uChromaticAberration;
uniform float uFilmGrain;
uniform float uTime;

vec3 sampleScene(vec2 uv) {
    vec2 direction = uv - 0.5;
    float aberration = uChromaticAberration * dot(direction, direction);
    float red = texture(uSceneTexture, uv + direction * aberration).r;
    float green = texture(uSceneTexture, uv).g;
    float blue = texture(uSceneTexture, uv - direction * aberration).b;
    return vec3(red, green, blue);
}

vec3 acesToneMap(vec3 color) {
    const float a = 2.51;
    const float b = 0.03;
    const float c = 2.43;
    const float d = 0.59;
    const float e = 0.14;
    return clamp((color * (a * color + b)) / (color * (c * color + d) + e), 0.0, 1.0);
}

float hash(vec2 point) {
    return fract(sin(dot(point, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    vec2 velocity = texture(uVelocityTexture, vTexCoord).xy * uMotionBlurStrength;
    vec3 scene = vec3(0.0);
    for (int i = 0; i < 5; ++i) {
        float offset = (float(i) / 4.0 - 0.5);
        scene += sampleScene(vTexCoord - velocity * offset);
    }
    scene /= 5.0;
    scene += texture(uBloomTexture, vTexCoord).rgb * uBloomStrength;
    scene *= max(uExposure, 0.0);
    scene = (scene - 0.5) * max(uContrast, 0.0) + 0.5;
    float luminance = dot(scene, vec3(0.2126, 0.7152, 0.0722));
    scene = mix(vec3(luminance), scene, max(uSaturation, 0.0));
    scene = acesToneMap(max(scene, vec3(0.0)));
    scene += (hash(gl_FragCoord.xy + uTime) - 0.5) * uFilmGrain;
    fragColor = vec4(clamp(scene, 0.0, 1.0), 1.0);
}
