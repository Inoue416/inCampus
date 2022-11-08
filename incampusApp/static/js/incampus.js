function changeForm(kind){
    const student_form_element = document.getElementById('collapseFormStudent');
    const teacher_form_element = document.getElementById('collapseFormTeacher');
    if (kind == 'student'){
        student_form_element.classList.add('show');
        teacher_form_element.classList.remove('show');
    }
    if (kind == 'teacher'){
        student_form_element.classList.remove('show');
        teacher_form_element.classList.add('show');
    }
}

function displayPassword(){
    const element = document.getElementById("displayCheck");
    element.addEventListener('change', function(event){
        const allElem = [];
        const passElem = document.getElementById("inputPassword");
        const confElem = document.getElementById("inputConfirmPassword");
        allElem.push(passElem);
        allElem.push(confElem);
        for (eachElem of allElem){
            if (eachElem != null){
                if (this.checked){
                    eachElem.setAttribute('type', 'text');
                } else{
                    eachElem.setAttribute('type', 'password');
                }        
            }
        }
    }, false);
}

jQuery( function($) {
    $('tbody tr[data-href]').addClass('clickable').click( function() {
        window.location = $(this).attr('data-href');
    }).find('a').hover( function() {
        $(this).parents('tr').unbind('click');
    }, function() {
        $(this).parents('tr').click( function() {
            window.location = $(this).attr('data-href');
        });
    });
});