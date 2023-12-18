function check_dup() {
    let username = $("#input-username").val();
    console.log(username);
    $("#help-id").addClass("is-loading");
    $.ajax({
        type: "POST",
        url: "/sign_up/check_dup",
        data: {
            username_give: username,
        },
        success: function (response) {
            console.log(response);
            if (response["exists"]) {
                alert("Thats Email alredy exists");
            } else {
                alert("Thats Email not used");
            }
        },
    });
}