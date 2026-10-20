#version 300 es
precision highp float;

in vec2 vNdc;
layout(location = 0) out vec4 fragColor;

uniform mat4 uInverseProjection;
uniform mat3 uCameraToWorld;
uniform vec3 uSunDirection;
uniform vec3 uZenithColor;
uniform vec3 uHorizonColor;
uniform vec3 uSunColor;
uniform float uAtmosphereDensity;

void main() {
    vec4 viewRay = uInverseProjection * vec4(vNdc, 1.0, 1.0);
    vec3 direction = normalize(uCameraToWorld * normalize(viewRay.xyz / viewRay.w));
    float elevation = clamp(direction.y * 0.5 + 0.5, 0.0, 1.0);
    float horizonFactor = pow(1.0 - elevation, max(uAtmosphereDensity, 0.01));
    vec3 sky = mix(uHorizonColor, uZenithColor, smoothstep(0.0, 1.0, elevation));
    float sun = pow(max(dot(direction, normalize(uSunDirection)), 0.0), 512.0);
    float halo = pow(max(dot(direction, normalize(uSunDirection)), 0.0), 24.0) * 0.08;
    sky = mix(sky, uHorizonColor, horizonFactor * 0.2);
    sky += uSunColor * (sun + halo);
    fragColor = vec4(max(sky, vec3(0.0)), 1.0);
}
