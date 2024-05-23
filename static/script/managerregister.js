function validateForm() {
    var firstName = document.getElementById('first-name').value;
    var lastName = document.getElementById('last-name').value;
    var email = document.getElementById('email').value;
    var phone = document.getElementById('phone').value;
    var dob = document.getElementById('dob').value;
    var username = document.getElementById('username').value;
    var password = document.getElementById('password').value;
    var cafeImage = document.getElementById('cafe-image').files[0]; // Get the cafe image file
    var isValid = true;
 
    // Example validation, you can add more validations as needed
    if (!firstName.trim()) {
       alert("First name is required");
       isValid = false;
    }
    if (!lastName.trim()) {
       alert("Last name is required");
       isValid = false;
    }
    if (!cafeImage) {
       alert("Cafe image is required");
       isValid = false;
    }

    // Validate email, phone, dob, username, password similarly
 
    return isValid;
}
