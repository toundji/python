function nextStep(stepNumber) {
    // 1. On cache toutes les étapes
    const steps = document.querySelectorAll('.form-step');
    steps.forEach(step => {
        step.style.display = 'none';
    });

    // 2. On affiche l'étape demandée
    const currentStep = document.getElementById('step' + stepNumber);
    if (currentStep) {
        currentStep.style.display = 'block';
        // 3. On remonte en haut pour que l'utilisateur voie le début
        window.scrollTo(0, 0);
    }
}

// Initialisation : on s'assure que seule l'étape 1 est visible au départ
document.addEventListener('DOMContentLoaded', () => {
    nextStep(1);
});
