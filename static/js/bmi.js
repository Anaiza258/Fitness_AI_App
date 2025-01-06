// document.addEventListener('DOMContentLoaded', function() {
//     // Get the elements after DOM is fully loaded
//     const heightInput = document.getElementById('height');
//     const weightInput = document.getElementById('weight');
//     const bmiOutput = document.getElementById('bmi');

//     // Check if all elements exist
//     if (!heightInput || !weightInput || !bmiOutput) {
//         console.error('One or more BMI-related elements are missing from the DOM.');
//         return;
//     }

//     function calculateBMI() {
//         const height = parseFloat(heightInput.value);
//         const weight = parseFloat(weightInput.value);

//         if (height > 0 && weight > 0) {
//             const bmi = (weight / ((height / 100) ** 2)).toFixed(2);
//             bmiOutput.value = bmi; // Display BMI
//             console.log('BMI value has been passed to the input field:', bmi); // Debug message inside the condition
//         } else {
//             bmiOutput.value = ''; // Clear if invalid
//             console.log('Invalid input. Please enter valid height and weight values.');
//         }
//     }

//     heightInput.addEventListener('input', calculateBMI);
//     weightInput.addEventListener('input', calculateBMI);
// });
