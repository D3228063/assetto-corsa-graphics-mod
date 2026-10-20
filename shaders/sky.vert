#version 300 es
precision highp float;

layout(location = 0) in vec2 aPosition;
out vec2 vNdc;

void main() {
    vNdc = aPosition;
    gl_Position = vec4(aPosition, 1.0, 1.0);
}
