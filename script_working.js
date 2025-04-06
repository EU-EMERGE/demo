// Funzione per caricare un file JSON
function loadJSON(file, callback) {
    let xhttp = new XMLHttpRequest();
    xhttp.open("GET", file, true);
    xhttp.onreadystatechange = function () {
        if (this.readyState == 4 && this.status == 200) {
            callback(JSON.parse(this.responseText));
        }
    };
    xhttp.send();
}

// Inizializzazione della rete neurale
let config = null;
let activations = null;
let canvas = document.getElementById('networkCanvas');
let ctx = canvas.getContext('2d');
let neurons = [];

// Global variables to store activation statistics
let prev_activations = null;


// Funzione per disegnare la rete neurale
function drawNetwork() {
    canvas.width = window.innerWidth * 0.8;
    canvas.height = window.innerHeight * 0.8;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    let layerWidth = canvas.width / (config.layers.length + 1);
    let maxNeurons = Math.max(...config.layers); // Get the maximum number of neurons in any layer
    neurons = []; // Reset neurons array

    // Calculate the total height of the tallest layer
    let totalHeight = maxNeurons * (canvas.height / (maxNeurons + 1));

    // Calculate the vertical offset to center the entire network in the canvas
    let networkVerticalOffset = -20;

    for (let i = 0; i < config.layers.length; i++) {
        let numNeurons = config.layers[i]; // Number of neurons in the current layer
        let layerHeight = canvas.height / (maxNeurons + 1);

        // Calculate vertical offset for the current layer
        let layerVerticalOffset = networkVerticalOffset + (canvas.height - (numNeurons * layerHeight)) / 2;

        for (let j = 0; j < numNeurons; j++) {
            let neuronX = (i + 1) * layerWidth;
            let neuronY = layerVerticalOffset + (j + 1) * layerHeight;

            // Draw the neuron
            ctx.beginPath();
            ctx.arc(neuronX, neuronY, 20, 0, Math.PI * 2);
            ctx.fillStyle = "#888"; // Base color (gray)
            ctx.fill();
            ctx.lineWidth = 2;
            ctx.strokeStyle = "#000";
            ctx.stroke();

            neurons.push({ x: neuronX, y: neuronY, layer: i, id: j });

            // Add input arrow for the first layer
            if (i === 0) {
                ctx.beginPath();
                ctx.moveTo(neuronX - 50, neuronY);
                ctx.lineTo(neuronX - 20, neuronY);
                ctx.lineWidth = 2;
                ctx.strokeStyle = "#ccc"; // Match connection color
                ctx.stroke();

                // Draw arrowhead
                ctx.beginPath();
                ctx.moveTo(neuronX - 25, neuronY - 5);
                ctx.lineTo(neuronX - 20, neuronY);
                ctx.lineTo(neuronX - 25, neuronY + 5);
                ctx.fillStyle = "#ccc"; // Match connection color
                ctx.fill();
            }

            // Add output arrow for the last layer
            if (i === config.layers.length - 1) {
                ctx.beginPath();
                ctx.moveTo(neuronX + 20, neuronY);
                ctx.lineTo(neuronX + 50, neuronY);
                ctx.lineWidth = 2;
                ctx.strokeStyle = "#ccc"; // Match connection color
                ctx.stroke();

                // Draw arrowhead
                ctx.beginPath();
                ctx.moveTo(neuronX + 45, neuronY - 5);
                ctx.lineTo(neuronX + 50, neuronY);
                ctx.lineTo(neuronX + 45, neuronY + 5);
                ctx.fillStyle = "#ccc"; // Match connection color
                ctx.fill();
            }
        }
    }

    // Draw the edges (connections) between neurons
    for (let i = 0; i < neurons.length; i++) {
        let neuron = neurons[i];
        if (neuron.layer < config.layers.length - 1) {
            let nextLayerNeurons = neurons.filter(n => n.layer === neuron.layer + 1);
            for (let nextNeuron of nextLayerNeurons) {
                ctx.beginPath();
                ctx.moveTo(neuron.x, neuron.y);
                ctx.lineTo(nextNeuron.x, nextNeuron.y);
                ctx.lineWidth = 1;
                ctx.strokeStyle = "#ccc"; // Light gray color for edges
                ctx.stroke();
            }
        }
    }
}

// Function to update neuron activations and change their colors based on activation values
function updateActivations(activations) {
    for (let i = 0; i < neurons.length; i++) {
        let neuron = neurons[i];
        let activationValue = activations[neuron.layer][neuron.id];

        // Debugging: Log activation values
        console.log(`Neuron [Layer ${neuron.layer}, ID ${neuron.id}] Activation: ${activationValue}`);

        // Ensure activationValue is valid
        if (isNaN(activationValue) || activationValue < 0) {
            activationValue = 0; // Default to 0 if invalid
        }

        let intensity = Math.min(1, Math.max(0, activationValue)); // Clamp intensity between 0 and 1
        let color = intensityToCoolWarm(intensity);

        // Change the neuron's color based on the activation
        ctx.beginPath();
        ctx.arc(neuron.x, neuron.y, 20, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = "#000";
        ctx.stroke();
    }
}

// Function to convert a normalized intensity (0 to 1) to a "coolwarm" color palette
function intensityToCoolWarm(intensity) {
    let norm = Math.min(1, Math.max(0, intensity)); // Ensure intensity is between 0 and 1
    let r, g, b;

    if (norm < 0.5) {
        // Interpolating blue -> white
        r = Math.floor(255 * (2 * norm));
        g = Math.floor(255 * (2 * norm));
        b = 255;
    } else {
        // Interpolating white -> red
        r = 255;
        g = Math.floor(255 * (2 - 2 * norm));
        b = Math.floor(255 * (2 - 2 * norm));
    }

    return `rgb(${r}, ${g}, ${b})`;
}

// Load configuration and initialize the network
loadJSON('config.json', function (data) {
    config = data;
    drawNetwork();
});

// Update activations periodically
setInterval(function () {
    loadJSON("activations.json", data => {
        updateActivations(data); // Update the visualization with averaged activations
    }) // Update the visualization
}, 100);