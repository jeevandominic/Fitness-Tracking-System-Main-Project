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
                }
            })
            .catch(error => console.error('Error:', error));
            
            input.value = '';
        }
    }
} 