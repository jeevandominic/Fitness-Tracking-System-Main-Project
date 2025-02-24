function likePost(postId, fromModal = false) {
    fetch(`/community/like/${postId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
        },
    })
    .then(response => response.json())
    .then(data => {
        if (fromModal) {
            const likeBtn = document.getElementById('modalLikeBtn');
            const likesCount = document.getElementById('modalLikesCount');
            likeBtn.classList.toggle('liked', data.status === 'liked');
            likesCount.textContent = data.likes;
        } else {
            const postCard = document.querySelector(`.post-card[data-post-id="${postId}"]`);
            const likeButton = postCard.querySelector('.like-btn');
            const likesCount = postCard.querySelector('.likes-count');
            
            if (data.status === 'liked') {
                likeButton.classList.add('liked');
            } else {
                likeButton.classList.remove('liked');
            }
            likesCount.textContent = data.likes;
        }
    })
    .catch(error => console.error('Error:', error));
}

function toggleComments(postId) {
    const commentsSection = document.getElementById(`comments-${postId}`);
    commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
}

function handleCommentSubmit(event, postId, fromModal = false) {
    if (event.key === 'Enter') {
        const input = event.target;
        const comment = input.value.trim();
        
        if (comment) {
            fetch(`/community/comment/${postId}/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `comment=${encodeURIComponent(comment)}`,
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    if (fromModal) {
                        openPostModal(postId); // Refresh the modal
                    } else {
                        window.location.reload(); // Refresh the page
                    }
                } else {
                    // Show error message
                    const errorDiv = document.createElement('div');
                    errorDiv.className = 'comment-error';
                    errorDiv.textContent = data.message;
                    input.parentNode.appendChild(errorDiv);
                    
                    // Remove error message after 3 seconds
                    setTimeout(() => {
                        errorDiv.remove();
                    }, 3000);
                }
            })
            .catch(error => console.error('Error:', error));
            
            input.value = '';
        }
    }
}

function handleImageSelect(input) {
    if (input.files && input.files[0]) {
        const reader = new FileReader();
        
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('imagePreview').style.display = 'block';
        };
        
        reader.readAsDataURL(input.files[0]);
    }
}

function removeImage() {
    const input = document.getElementById('image');
    const preview = document.getElementById('imagePreview');
    
    input.value = '';
    preview.style.display = 'none';
}

let cropper = null;
let currentFilter = 'normal';

function editExistingImage() {
    console.log('Edit button clicked'); // Debug log
    
    const previewImg = document.getElementById('previewImg');
    const imageToEdit = document.getElementById('imageToEdit');
    const modal = document.getElementById('imageEditorModal');

    if (!previewImg.src) {
        console.log('No image to edit');
        return;
    }

    // Set the image source
    imageToEdit.src = previewImg.src;
    
    // Show the modal
    modal.style.display = 'block';
    
    // Wait for image to load before initializing cropper
    imageToEdit.onload = function() {
        console.log('Image loaded, initializing cropper');
        initializeCropper();
    };
}

function initializeCropper() {
    console.log('Initializing cropper'); // Debug log
    const image = document.getElementById('imageToEdit');
    
    if (cropper) {
        cropper.destroy();
    }

    try {
        cropper = new Cropper(image, {
            viewMode: 2,
            dragMode: 'move',
            autoCropArea: 1,
            restore: false,
            modal: true,
            guides: true,
            highlight: true,
            cropBoxMovable: true,
            cropBoxResizable: true,
            toggleDragModeOnDblclick: true,
            ready: function() {
                console.log('Cropper is ready');
            }
        });
    } catch (error) {
        console.error('Error initializing cropper:', error);
    }
}

function enableCrop() {
    if (cropper) {
        cropper.setDragMode('crop');
    }
}

function rotateImage(degree) {
    if (cropper) {
        cropper.rotate(degree);
    }
}

function resetCrop() {
    if (cropper) {
        cropper.reset();
        applyFilter('normal');
    }
}

function applyFilter(filter) {
    if (!cropper) return;
    
    const image = cropper.getCanvasData().el;
    currentFilter = filter;
    
    // Remove all previous filters
    image.style.filter = '';
    
    // Apply selected filter
    switch(filter) {
        case 'grayscale':
            image.style.filter = 'grayscale(100%)';
            break;
        case 'sepia':
            image.style.filter = 'sepia(100%)';
            break;
        case 'brightness':
            image.style.filter = 'brightness(130%)';
            break;
        case 'contrast':
            image.style.filter = 'contrast(150%)';
            break;
        case 'warmth':
            image.style.filter = 'sepia(50%) saturate(150%)';
            break;
    }
    
    // Update active filter button
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[onclick="applyFilter('${filter}')"]`).classList.add('active');
}

function saveEditedImage() {
    if (!cropper) return;
    
    const canvas = cropper.getCroppedCanvas({
        maxWidth: 2048,
        maxHeight: 2048,
        fillColor: '#fff',
        imageSmoothingEnabled: true,
        imageSmoothingQuality: 'high',
    });
    
    // Apply current filter to canvas
    if (currentFilter !== 'normal') {
        const context = canvas.getContext('2d');
        context.filter = document.getElementById('imageToEdit').style.filter;
        context.drawImage(canvas, 0, 0);
        context.filter = 'none';
    }
    
    canvas.toBlob((blob) => {
        const fileName = 'edited_' + Date.now() + '.jpg';
        const file = new File([blob], fileName, { type: 'image/jpeg' });
        
        // Update the file input
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        document.getElementById('image').files = dataTransfer.files;
        
        // Update preview
        const reader = new FileReader();
        reader.onload = function(e) {
            document.getElementById('previewImg').src = e.target.result;
            document.getElementById('imagePreview').style.display = 'block';
        };
        reader.readAsDataURL(file);
        
        closeImageEditor();
    }, 'image/jpeg', 0.92);
}

// Add this function to handle button clicks
function handleButtonClick(event) {
    event.preventDefault();
    event.stopPropagation();
    const action = event.currentTarget.getAttribute('data-action');
    if (action === 'edit') {
        editExistingImage();
    } else if (action === 'remove') {
        removeImage();
    }
}

// Update the initialization code
document.addEventListener('DOMContentLoaded', function() {
    // Initialize buttons
    const editBtn = document.querySelector('.edit-image-btn');
    const removeBtn = document.querySelector('.remove-image');
    
    if (editBtn) {
        editBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            console.log('Edit button clicked');
            editExistingImage();
        });
    }
    
    if (removeBtn) {
        removeBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            removeImage();
        });
    }

    // Modal close handlers
    const closeBtn = document.querySelector('.close-modal');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeImageEditor);
    }
    
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('imageEditorModal');
        if (event.target === modal) {
            closeImageEditor();
        }
    });
});

function closeImageEditor() {
    const modal = document.getElementById('imageEditorModal');
    modal.style.display = 'none';
    
    if (cropper) {
        cropper.destroy();
        cropper = null;
    }
} 